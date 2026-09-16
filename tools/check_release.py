"""Fail-closed checks for the research publication boundary and commit identity."""
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tomllib
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
IDENTITY=('blackscaletech','6562904+blackscaletech@users.noreply.github.com')
PATTERNS={
 'user_directory':r'(?:/Users/|/home/)[A-Za-z0-9_.-]+',
 'os_private_directory':r'/(?:private/tmp|(?:private/)?var/folders)/',
 'windows_user_directory':r'[A-Za-z]:[\\/]+Users[\\/]+[^\s\\/]+',
 'private_key':r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
 'github_token':r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b',
 'api_token':r'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}',
 'aws_key':r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
 'credential_url':r'https?://[^\s/:]+:[^\s/@]+@',
 'disallowed_identity':'hello'+'reila',
}
SKIP={'.git','__pycache__','.venv','build','dist','.pytest_cache'}

def git(*args,check=True):
    result=subprocess.run(['git',*args],cwd=ROOT,capture_output=True,check=check)
    return result.stdout

def inspect_bytes(name,data):
    texts=[data.decode('utf-8',errors='ignore')]
    if name.endswith('.pdf'):
        pdf=PdfReader(io.BytesIO(data))
        assert not pdf.is_encrypted,'Encrypted PDF is outside release policy'
        assert not pdf.attachments,'Embedded PDF attachments are outside release policy'
        texts.extend([json.dumps(dict(pdf.metadata or {}))]+[p.extract_text() for p in pdf.pages])
        if name.endswith('IWU-RESEARCH-BRIEF.pdf'):
            assert pdf.metadata.author=='Swarm Research'
            assert len(pdf.pages)==5
            for page in pdf.pages:
                assert 'swarm.services' in page.extract_text()
                uris=[a.get_object().get('/A',{}).get('/URI') for a in page.get('/Annots',[])]
                assert 'https://swarm.services' in uris
            text=' '.join(texts)
            for phrase in ['public licensing remain pending','Public posting awaits approval','Substantial AI assistance','conducted outside Swarm']:
                assert phrase not in text,'Internal publication wording in paper'
            assert 'Inference Work Units' in text
    if name.endswith('artifacts-base64.json'):
        texts += [base64.b64decode(v,validate=True).decode('utf-8',errors='ignore') for v in json.loads(data).values()]
    for text in texts:
        for label,pattern in PATTERNS.items():
            assert not re.search(pattern,text,re.I if label=='disallowed_identity' else 0),f'{name}: {label}'

def current_files():
    found=[]
    for parent,dirs,files in os.walk(ROOT,followlinks=False):
        for d in list(dirs):
            p=Path(parent)/d
            assert not p.is_symlink(),f'Symlink directory: {p.name}'
            if d in SKIP or d.endswith('.egg-info'):dirs.remove(d)
            elif d in {'private','.codex','.ssh','.aws'}:raise AssertionError('Forbidden directory class')
        for name in files:
            p=Path(parent)/name;rel=p.relative_to(ROOT).as_posix()
            assert not p.is_symlink(),f'Symlink file: {rel}'
            if rel=='sources/metr_runs.jsonl':continue
            found.append(rel)
    return sorted(found)

def main():
    if not __debug__:raise RuntimeError('Release checks require assertions enabled')
    parser=argparse.ArgumentParser();parser.add_argument('--history',action='store_true');args=parser.parse_args()
    allowed=json.loads((ROOT/'RELEASE-FILES.json').read_text())
    assert len(set(allowed))==len(allowed)
    assert current_files()==sorted(allowed),'Working-tree content differs from explicit release allowlist'
    manifest=json.loads((ROOT/'RELEASE-MANIFEST.json').read_text())
    expected={x['path']:x['sha256'] for x in manifest['files']}
    assert set(expected)==set(allowed)-{'RELEASE-MANIFEST.json'}
    for name in allowed:
        data=(ROOT/name).read_bytes();inspect_bytes(name,data)
        if name in expected:assert hashlib.sha256(data).hexdigest()==expected[name],f'Changed release content: {name}'
        assert not any(x in name.lower() for x in ['x-post','x-thread','x-article','social-card','launch-checklist','marketing'])
    version=(ROOT/'VERSION').read_text().strip()
    assert re.fullmatch(r'(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-rc\.(?:0|[1-9]\d*))?',version)
    project=tomllib.loads((ROOT/'pyproject.toml').read_text())['project']
    assert project['version']==version.replace('-rc.','rc')
    assert project['authors']==[{'name':'blackscaletech'}]
    assert 'version: '+version in (ROOT/'CITATION.cff').read_text()
    assert manifest['version']==version
    history_blobs=0
    if args.history:
        records=git('log','--all','--format=%an%x09%ae%x09%cn%x09%ce%x09%B%x00').decode().split('\x00')
        assert records and records[0].strip(),'History check requires an initial commit'
        for row in records:
            if not row.strip():continue
            fields=row.strip().split('\t',4)
            assert tuple(fields[:2])==IDENTITY and tuple(fields[2:4])==IDENTITY,'Unexpected author or committer'
            assert 'co-authored-by:' not in fields[4].lower(),'Unexpected coauthor trailer'
            inspect_bytes('commit-message',fields[4].encode())
        for line in git('for-each-ref','--format=%(objectname)%09%(objecttype)%09%(taggername)%09%(taggeremail)','refs/tags').decode().splitlines():
            if not line.strip():continue
            fields=line.split('\t',3)
            assert fields[1]=='tag','Release tags must be annotated'
            assert (fields[2],fields[3].strip('<>'))==IDENTITY,'Unexpected release tagger'
            inspect_bytes('tag-message',git('cat-file','-p',fields[0]))
        seen=set()
        for line in git('rev-list','--objects','--all').decode().splitlines():
            oid,_,name=line.partition(' ')
            if oid in seen:continue
            seen.add(oid)
            if git('cat-file','-t',oid).strip()!=b'blob':continue
            assert name in allowed,f'Unlisted historical blob: {name}'
            inspect_bytes(name,git('cat-file','-p',oid));history_blobs+=1
        tracked=set(git('ls-files','-z').decode().strip('\x00').split('\x00'))
        assert tracked==set(allowed),'Git index differs from the release allowlist'
        assert not git('status','--porcelain'),'Working tree must be clean for a release check'
    print(json.dumps({'version':version,'release_files':len(allowed),'history_blobs_checked':history_blobs,
        'expected_contributor':IDENTITY[0],'content_and_integrity_checks':'passed'},indent=2))

if __name__=='__main__':main()
