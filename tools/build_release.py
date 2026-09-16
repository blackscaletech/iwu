"""Generate deterministic local release artifacts from the explicit file allowlist."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--refresh-manifest',action='store_true');args=parser.parse_args()
    paths=json.loads((ROOT/'RELEASE-FILES.json').read_text())
    version=(ROOT/'VERSION').read_text().strip()
    if args.refresh_manifest:
        provenance=json.loads((ROOT/'sources/PROVENANCE.json').read_text())
        selection=json.loads((ROOT/'SELECTION-LOCK.json').read_text())
        result={'version':version,'publisher':'Swarm Research','maintainer':'blackscaletech',
            'source_revision':provenance['revision'],'source_sha256':provenance['sha256'],
            'historical_protocol_sha256':selection['protocol_sha256'],
            'files':[{'path':p,'bytes':(ROOT/p).stat().st_size,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()}
                     for p in paths if p!='RELEASE-MANIFEST.json']}
        (ROOT/'RELEASE-MANIFEST.json').write_text(json.dumps(result,indent=2)+'\n')
    from check_release import main as check
    import sys
    original=sys.argv;sys.argv=[sys.argv[0]]
    try:check()
    finally:sys.argv=original
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    dest=dist/f'iwu-{version}.zip'
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in paths:
            info=zipfile.ZipInfo(f'iwu-{version}/{p}',(2026,9,15,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o755 if p=='.githooks/pre-push' else 0o644)<<16
            z.writestr(info,(ROOT/p).read_bytes())
    with zipfile.ZipFile(dest) as z:assert z.testzip() is None
    digest=hashlib.sha256(dest.read_bytes()).hexdigest()
    (dist/'SHA256SUMS').write_text(f'{digest}  {dest.name}\n')
    print(json.dumps({'archive':dest.name,'sha256':digest,'files':len(paths)}))

if __name__=='__main__':main()
