import copy
import hashlib
import random
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from iwu import InvalidLedger
from trace_audit import audit,credit_atoms


def fixture():
    blobs=[b"question",b"answer",b"accepted"]
    hashes=[hashlib.sha256(x).hexdigest() for x in blobs]
    trace=dict(registry_sha256="a"*64,task_version_sha256="b"*64,system_config_sha256="c"*64,
        episode_id="one",effective_model="fixed",expected_model="fixed",
        effective_effort="medium",expected_effort="medium",declared_inputs=[hashes[0]],
        allowed_tools=["calculator"],expected_span_ids=["root","solve","verify"],
        executor_forbidden_inputs=[],
        final_artifact_sha256=hashes[1],verification_artifact_sha256=hashes[2],spans=[
        dict(span_id="root",parent_id=None,predecessor_ids=[],kind="episode",start_ns=0,end_ns=100,
             consumes=[],produces=[]),
        dict(span_id="solve",parent_id="root",predecessor_ids=[],kind="model",model="fixed",effort="medium",
             start_ns=1,end_ns=90,consumes=[hashes[0]],produces=[hashes[1]]),
        dict(span_id="verify",parent_id="root",predecessor_ids=["solve"],kind="verify",
             start_ns=90,end_ns=99,consumes=[hashes[1]],produces=[hashes[2]])])
    return trace,dict(zip(hashes,blobs))


class TraceTests(unittest.TestCase):
    def test_valid_trace(self):self.assertEqual(audit(*fixture())["structural_audit"],"passed")
    def test_tampered_artifact(self):
        t,b=fixture();b[t["final_artifact_sha256"]]=b"different"
        with self.assertRaises(InvalidLedger):audit(t,b)
    def test_missing_artifact(self):
        t,b=fixture();del b[t["final_artifact_sha256"]]
        with self.assertRaises(InvalidLedger):audit(t,b)
    def test_future_context(self):
        t,b=fixture();t["spans"][1]["consumes"].append(t["verification_artifact_sha256"])
        with self.assertRaises(InvalidLedger):audit(t,b)
    def test_missing_predecessor(self):
        t,b=fixture();t["spans"][2]["predecessor_ids"]=[]
        with self.assertRaises(InvalidLedger):audit(t,b)
    def test_declared_rubric_leakage(self):
        t,b=fixture();t["executor_forbidden_inputs"]=list(t["declared_inputs"])
        with self.assertRaises(InvalidLedger):audit(t,b)
    def test_multiple_roots(self):
        t,b=fixture();t["spans"][1]["parent_id"]=None
        with self.assertRaises(InvalidLedger):audit(t,b)
    def test_model_drift(self):
        t,b=fixture();t["effective_model"]="other"
        with self.assertRaises(InvalidLedger):audit(t,b)
    def test_missing_model_attestation(self):
        t,b=fixture();t["effective_model"]=None
        with self.assertRaises(InvalidLedger):audit(t,b)
    def test_effort_drift(self):
        t,b=fixture();t["spans"][1]["effort"]="high"
        with self.assertRaises(InvalidLedger):audit(t,b)
    def test_route_drift(self):
        t,b=fixture();t["spans"][1].update(kind="tool",tool_name="web_search")
        with self.assertRaises(InvalidLedger):audit(t,b)
    def test_duplicate_span(self):
        t,b=fixture();t["spans"].append(t["spans"][1])
        with self.assertRaises(InvalidLedger):audit(t,b)
    def test_missing_span(self):
        t,b=fixture();t["spans"].pop()
        with self.assertRaises(InvalidLedger):audit(t,b)
    def test_reasoning_text_rejected(self):
        t,b=fixture();t["spans"][1]["reasoning_text"]="not part of this format"
        with self.assertRaises(InvalidLedger):audit(t,b)
    def test_timestamp_causality(self):
        t,b=fixture();t["spans"][2]["start_ns"]=80
        with self.assertRaises(InvalidLedger):audit(t,b)
    def test_atom_double_credit(self):
        with self.assertRaises(InvalidLedger):credit_atoms(10,[dict(atom_id="a",fraction=1,accepted=True)]*2)
    def test_atom_weight_inflation(self):
        with self.assertRaises(InvalidLedger):credit_atoms(10,[dict(atom_id="a",fraction=1,accepted=True),dict(atom_id="b",fraction=1,accepted=True)])
    def test_randomized_atom_conservation(self):
        rng=random.Random(17)
        for case in range(1000):
            with self.subTest(case=case):
                count=rng.randint(2,50);weights=[rng.random()+.001 for _ in range(count)];total=sum(weights)
                atoms=[dict(atom_id=str(i),fraction=w/total,accepted=True) for i,w in enumerate(weights)]
                self.assertAlmostEqual(credit_atoms(60,atoms),60)
                atoms[0]["accepted"]=False
                self.assertAlmostEqual(credit_atoms(60,atoms),60*(1-weights[0]/total))


if __name__=="__main__":unittest.main()
