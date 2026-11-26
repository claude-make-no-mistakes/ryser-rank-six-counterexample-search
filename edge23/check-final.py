from itertools import product, combinations
from pathlib import Path
import json


ps=[[8,6,3,2,2,2],[7,7,3,2,2,2],[8,5,3,3,2,2],[8,5,3,3,2,2],[8,4,3,3,3,2],[8,3,3,3,3,3]]
pats=[[15,23,27,39,43,60,60,49],[15,23,27,46,53,57,60,35],[15,30,39,43,53,57,60,19]]
coeff_a=[4,3,0,3,0,-1,-5,3,2,0,2,3,2,0,2,0,-1,-2,-1,0,0]
coeff_b=[4,3,0,3,-1,-2,-6,3,2,0,2,3,2,0,2,0,0,-1,0,0,0]
certs=[coeff_a+[3,3,3,3,3,-2,-2,-3,0], coeff_b+[3,3,3,3,-2,-2,-2,2,0], coeff_a+[3,3,3,3,-2,-2,-2,2,0]]
pairs=[(1<<i)|(1<<j) for i,j in combinations(range(6),2)]
mins=[4,3,3,3,3,3,3,2,2,3,3,3,3,3,3]
systems=json.loads((Path(__file__).resolve().parent/'systems-17.json').read_text())
assert len(systems)==17 and systems[4][0]==ps and systems[4][1:3]==[276,11]
assert systems[4][-1]==mins
from itertools import combinations_with_replacement
found=[]
for chosen in combinations_with_replacement([i for i in range(64) if i.bit_count()==4],7):
  left=[l-sum(x&p==p for x in chosen) for p,l in zip(pairs,mins)]
  need=sum(max(x,0) for x in left)
  if need==2 and min(left)>=0:
    found.append(list(chosen)+[p for p,count in zip(pairs,left) for _ in range(count)])
  if need<=3 and max(left)<=1:
    for m3 in range(64):
      if m3.bit_count()==3 and all(x<=0 or m3&p==p for x,p in zip(left,pairs)):
        found.append(list(chosen)+[m3])
assert found==pats,found
ts=[sorted(set(p)) for p in ps]
cols=[(i,d) for i,p in enumerate(ts) for d in p]
b=[ps[i].count(d)*d for i,d in cols]
for index,pattern in enumerate(pats):
  d0=pattern[-1]
  row=[]
  C={J:sum((pattern[j].bit_count()-1) for j in J) for k in range(4) for J in combinations(range(8),k)}
  C={J:r for J,r in C.items() if (len(J)<=1 or len(J)==2 and (7 in J or pattern[J[0]]&pattern[J[1]]==d0))}
  for a in product(*ts):
    n2=a.count(2)
    if n2>1:continue
    r=sum(a)-28
    if r<0:continue
    for J,v in C.items():
      if v!=r:continue
      counts=[sum(bool(pattern[j]&(1<<i)) for j in J) for i in range(6)]
      caps=[d-(3 if n2 else 2) if d>=4 else 0 for d in a]
      if any(x>y for x,y in zip(counts,caps)):continue
      priv=[d-1-c for d,c in zip(a,counts)]
      if any(sum(priv[i] for i in range(6) if S&(1<<i))+sum((pattern[j]&S)==pattern[j] for j in J)<[0,1,3,5,9,14,22][S.bit_count()] for S in range(1,63)):continue
      row.append((a,J))
  A=[[int(a[i]==d) for a,J in row] for i,d in cols]
  A+=[[int(j in J) for a,J in row] for j in range(8)]
  A.append([int(len(J)==2 and 7 not in J) for a,J in row])
  B=b+[2]*8
  coefficients=certs[index]
  assert len(coefficients)==len(A) and coefficients[-1]<=0
  assert max(sum(x*y for x,y in zip(coefficients,col)) for col in zip(*A))<=0
  value=sum(x*y for x,y in zip(coefficients,B+[1]))
  assert value==[55,53,55][index]
  print(pattern,len(row),value)
