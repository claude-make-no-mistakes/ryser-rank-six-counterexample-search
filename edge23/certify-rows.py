import json
from pathlib import Path
from fractions import Fraction
from math import lcm, inf
from functools import reduce
from itertools import product
import sys
here=Path(__file__).resolve().parent
systems=json.loads((here/'systems-17.json').read_text())
records=[]
check_only='--check' in sys.argv
if check_only:
  saved=json.loads((here/'row-duals.json').read_text())
else:
  from scipy.optimize import linprog
for ix,(ps,s,t,_,pair_minima) in enumerate(systems):
  R=s-253
  L=sum(pair_minima)
  ts=[sorted(set(p)) for p in ps]
  row=[]
  counts=[]
  for a in product(*ts):
    n2=a.count(2)
    if n2>1:continue
    r=sum(a)-28
    if r<0:continue
    caps=[d-(3 if n2 else 2) if d>=4 else 0 if n2 or t==11 else d-2 for d in a]
    best=inf
    for h4 in range(r//3+1):
      for h3 in range((r-3*h4)//2+1):
        h2=r-3*h4-2*h3
        ns=h2+h3+h4
        if 4*h4 > sum(min(c,h4) for c in caps):continue
        if 4*h4+3*h3 > sum(min(c,h4+h3) for c in caps):continue
        if r+ns > sum(min(c,ns) for c in caps):continue
        best=min(best,h2+h3)
    if best==inf:continue
    row.append(a)
    counts.append(best)
  ts=[(i,d) for i,p in enumerate(ts) for d in p]
  b=[ps[i].count(d)*d for i,d in ts]
  A=[[int(a[i]==d) for a in row] for i,d in ts]
  if check_only:
    denominator=saved[ix]['denominator']
    integers=saved[ix]['coefficients']
  else:
    out=linprog(counts,A_eq=A,b_eq=b,bounds=(0,None),method='highs')
    assert out.status==0
    fractions=[Fraction(float(x)).limit_denominator(1000) for x in out.eqlin.marginals]
    denominator=reduce(lcm, (x.denominator for x in fractions), 1)
    integers=[int(x*denominator) for x in fractions]
  assert denominator>0 and len(integers)==len(b)
  assert all(sum(x*a for x,a in zip(integers,column)) <= denominator*value for column,value in zip(zip(*A),counts))
  value=sum(x*a for x,a in zip(integers,b))
  limit=2*(2*R-L)
  records.append({'index':ix, 'denominator':denominator,'coefficients':integers,'value':value,'limit':limit,'rows':len(row)})
  print(ix,len(row),str(Fraction(value,denominator)),limit,flush=True)
assert [r['index'] for r in records if r['value']<=r['denominator']*r['limit']]==[4]
if check_only:
  assert records==saved
else:
  (here/'row-duals.json').write_text(json.dumps(records,indent=2)+'\n')
