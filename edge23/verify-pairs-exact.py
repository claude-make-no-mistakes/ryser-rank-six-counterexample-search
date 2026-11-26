from itertools import combinations
from functools import cache
from scipy.optimize import linprog
from fractions import Fraction
from math import ceil
from scipy.sparse import csr_matrix
import numpy as np
import json
from pathlib import Path
from math import comb, inf
from time import time

here=Path(__file__).resolve().parent

data=json.loads((here/'systems-126.json').read_text())
RANK=6
cut={2:9,3:5,4:3,5:1}

@cache
def pair(p,q,strict):
    n,m=len(p),len(q)
    lo=[[max(0,a+b-14) for b in q] for a in p]
    hi=[[0 if a==b==2 else 1 if min(a,b)==2 or strict and min(a,b)==3 else min(a,b)-1 for b in q] for a in p]
    if any(lo[i][j]>hi[i][j] for i in range(n) for j in range(m)):
      return inf
    a=[d-sum(lo[i]) for i,d in enumerate(p)]
    b=[d-sum(lo[i][j] for i in range(n)) for j,d in enumerate(q)]
    if min(a+b)<0:return inf
    idx=[(i,j,k) for i in range(n) for j in range(m) for k in range(lo[i][j],hi[i][j])]
    cs=[k for _,_,k in idx]
    A=[[int(i==u) for u,v,k in idx] for i in range(n)]+[[int(j==v) for u,v,k in idx] for j in range(m)]
    lb=a+b
    ub=a+b
    for i in range(1,5):
     for j in range(1,6-i):
      if i+j<3:continue
      for rr in combinations(range(n),i):
       for cc in combinations(range(m),j):
        target=(sum(p[u] for u in rr)+sum(q[v] for v in cc)-23+cut[i+j]
                -sum(lo[u][v] for u in rr for v in cc))
        if target>0:
         w=[int(u in rr and v in cc) for u,v,k in idx]
         if sum(w)<target:return inf
         A.append(w)
         lb.append(target)
         ub.append(inf)
    matrix=csr_matrix(A)
    rr=linprog(cs,A_eq=matrix[:n+m],b_eq=lb[:n+m],
               A_ub=-matrix[n+m:],b_ub=-np.array(lb[n+m:]),bounds=(0,1),method='highs')
    assert rr.status==0
    ys,zs,ws=[[Fraction(float(x)).limit_denominator(1000) for x in v] for v in
              (rr.eqlin.marginals, rr.ineqlin.marginals, rr.upper.marginals)]
    yl=ys+[-z for z in zs]
    assert max(zs+ws)<=0
    assert all(w+sum(yy*x for yy,x in zip(yl,col))<=c for c,w,col in zip(cs,ws,zip(*A)))
    value=sum(y*b for y,b in zip(yl,lb))+sum(ws)
    return ceil(value)+sum(comb(x,2) for row in lo for x in row)


J=list(combinations(range(6),2))
@cache
def exact_support(limits,two_sides,strict,R):
  K=[p for k in range(2,5) for p in combinations(range(6),k)
     if k<4 or not strict or any(i not in p for i in two_sides)]
  supports=[(len(p)-1,tuple(i for i,q in enumerate(J) if set(q)<=set(p))) for p in K]
  cand=[sorted([(c,ss) for c,ss in supports if i in ss],reverse=True) for i in range(15)]
  at=[[j for j,(x,y) in enumerate(J) if i in (x,y)] for i in range(6)]
  failed={}
  def search(left,r):
    if not any(left):return True
    if r*2 < sum(left) or any(sum(left[j] for j in a)>r for a in at):return False
    if failed.get(left,-1)>=r:return False
    def applicable(i):
      return [(cost,S) for cost,S in cand[i]
              if cost<=r and sum(left[j]>0 for j in S)>=sum(left)-2*(r-cost)]
    pivot=max(range(15),key=lambda j:(bool(left[j]),left[j],-len(cand[j])))
    for cost,S in applicable(pivot):
      nxt=list(left)
      for j in S:nxt[j]=max(0,nxt[j]-1)
      if search(tuple(nxt),r-cost):return True
    failed[left]=max(failed.get(left,0),r)
    return False
  return search(limits,R)

keep=[]
pair_mins=[]
countpass=0
start=time()
for k,(p,s,t,l) in enumerate(data):
 p=[tuple(v) for v in p]
 ls=[pair(*sorted((a,b)),t==11) for a,b in combinations(p,2)]
 if sum(ls)<=2*(s-253):
  countpass+=1
  r=s-253
  ts=[q.count(2) for q in p]
  if exact_support(tuple(ls),tuple(i for i in range(6) if ts[i]),t==11,r):
   keep.append(k)
   pair_mins.append(ls)
print('hard transport pass',countpass,flush=True)
print('kept',len(keep),'seconds',time()-start,'cache',pair.cache_info(),flush=True)
print(keep,flush=True)

assert countpass==72 and len(keep)==17
(here/'systems-17.json').write_text(json.dumps([[*data[i],ls] for i,ls in zip(keep,pair_mins)],indent=2)+'\n')
