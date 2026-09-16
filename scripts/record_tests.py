import io
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]


def main():
    stream=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(ROOT/"tests"))
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    doc=dict(test_methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),
             skipped=len(result.skipped),passed=result.wasSuccessful(),
             deterministic_randomized_cases=3000,independent_live_key_checks=12,
             independent_external_reviewer=False,
             scope="Software/accounting and structural evidence fixtures; no external certification")
    (ROOT/"results").mkdir(exist_ok=True)
    (ROOT/"results/TESTS.json").write_text(json.dumps(doc,indent=2)+"\n")
    # Strip timing footer: deterministic test names/results, no volatile wall-clock claims.
    lines=[s for s in stream.getvalue().splitlines() if s.startswith("test_")]
    (ROOT/"results/TEST-LOG.txt").write_text("\n".join(lines)+"\n")
    print(json.dumps(doc,indent=2))
    if not result.wasSuccessful():print(stream.getvalue());raise SystemExit(1)


if __name__=="__main__":main()
