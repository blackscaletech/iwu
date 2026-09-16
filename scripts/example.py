"""Verify the golden accounting and trace fixtures without model or network calls."""
import base64
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from iwu import calculate
from trace_audit import audit

def main():
    def load(name):return json.loads((ROOT/'examples'/f'{name}.json').read_text())
    score=calculate(load('registry'),load('assignments'),load('ledger'))
    assert score==load('expected-score')
    audit(load('trace'),{k:base64.b64decode(v,validate=True) for k,v in load('artifacts-base64').items()})
    print(json.dumps(score,indent=2))

if __name__=='__main__':main()
