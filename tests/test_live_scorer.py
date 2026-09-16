import ast
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from live_smoke import generate


def independent_answer(task):
    q=task["question"]
    if task["family"]=="arithmetic":
        tree=ast.parse(q.removeprefix("Compute the integer value of ").removesuffix("."),mode="eval")
        def value(n):
            if isinstance(n,ast.Expression):return value(n.body)
            if isinstance(n,ast.Constant):return n.value
            a,b=value(n.left),value(n.right)
            return a+b if isinstance(n.op,ast.Add) else a-b if isinstance(n.op,ast.Sub) else a*b
        return value(tree)
    if task["family"]=="shortest_path":
        edges=json.JSONDecoder().raw_decode(q[q.index(": ")+2:])[0]
        d=[[0 if i==j else 10**12 for j in range(8)] for i in range(8)]
        for i,j,w in edges:d[i][j]=min(d[i][j],w)
        for k in range(8):
            for i in range(8):
                for j in range(8):d[i][j]=min(d[i][j],d[i][k]+d[k][j])
        return d[0][7]
    items=json.JSONDecoder().raw_decode(q[q.index(": ")+2:])[0]
    dp={(0,0,0):0}
    for ident,w,v in items:
        new=dict(dp)
        for (weight,count,evens),val in dp.items():
            if weight+w<=22 and count+1<=6:
                key=(weight+w,count+1,min(2,evens+(ident%2==0)))
                new[key]=max(new.get(key,-1),val+v)
        dp=new
    return max(val for (w,c,e),val in dp.items() if 4<=c<=6 and e==2)


class ScorerTests(unittest.TestCase):
    def test_independent_scoring_keys(self):
        tasks,key=generate()
        for task in tasks:
            with self.subTest(task=task["id"]):self.assertEqual(independent_answer(task),key[task["id"]])
    def test_generator_reproducibility(self):self.assertEqual(generate(),generate())


if __name__=="__main__":unittest.main()
