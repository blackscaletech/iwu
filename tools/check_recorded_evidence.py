"""Independently rescore the archived smoke-test answers and golden examples."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))

def main():
    spec=importlib.util.spec_from_file_location('live_key_check',ROOT/'tests/test_live_scorer.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    tasks=json.loads((ROOT/'live/TASKS.json').read_text())
    keys=json.loads((ROOT/'live/SCORING-KEY.json').read_text())
    assert {t['id']:mod.independent_answer(t) for t in tasks}==keys
    live=json.loads((ROOT/'live/RESULTS.json').read_text());accepted=0;answers=0
    for run in live['runs']:
        candidate=run['final_answer']['answers']
        assert set(candidate)==set(keys)
        score=sum(type(candidate[k]) is int and candidate[k]==v for k,v in keys.items())
        assert score==run['accepted_count']
        accepted+=score;answers+=len(keys)
    assert len(live['runs'])==6 and answers==72 and accepted==72
    from example import main as golden
    golden()
    print(json.dumps({'independently_checked_keys':len(keys),'recorded_answers':answers,'accepted':accepted}))

if __name__=='__main__':main()
