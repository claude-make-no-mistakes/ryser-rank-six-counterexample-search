"use strict";
const fs = require("node:fs");
const path = require("node:path");
const { exam, costs } = (() => {

function C(n) { return n*(n-1)/2; }
function profiles(n, maximumDegree) {
  const ps=[];
  function extend(left, cap, p) {
    if(left===0) { if(p.length>=6&&p[0]+p[1]<=n-9) ps.push(p); return; }
    for(let d=Math.min(cap,left);d>=2;d--) extend(left-d,d,p.concat(d));
  }
  extend(n,maximumDegree,[]);
  return ps.map(p=>({p,s:p.reduce((a,d)=>a+C(d),0),t:p.filter(d=>d===2).length})).sort((a,b)=>b.s-a.s);
}
function costs(n,ps,d3,unpaired=null) {
  function min(p,q) {
    const a=p.p.slice(), b=q.p.slice(), m=a.length, k=b.length;
    const src=m+k, sink=src+1, size=sink+1, g=Array.from({length:size},()=>[]);
    function edge(u,v,capacity,cost) {
      const x={v,capacity,cost}, y={v:u,capacity:0,cost:-cost};
      x.back=y;y.back=x;g[u].push(x);g[v].push(y);
    }
    let ans=0;
    for(let i=0;i<m;i++) for(let j=0;j<k;j++) {
      const lo=Math.max(0,p.p[i]+q.p[j]-(n-9));
      const di=p.p[i], dj=q.p[j];
      let hi=di===2||dj===2 ? (di===dj?0:1) : d3&&(di===3||dj===3)?1:Math.min(di,dj)-1;
      if (unpaired !== null && Math.min(di,dj)>=3) {
        if (di-1>unpaired) hi=Math.min(hi,di-2);
        if (dj-1>unpaired) hi=Math.min(hi,dj-2);
      }
      if(lo>hi)return Infinity;
      a[i]-=lo;b[j]-=lo;
      ans+=C(lo);
      for(let z=lo;z<hi;z++) edge(i,m+j,1,z);
    }
    if(a.some(x=>x<0)||b.some(x=>x<0))return Infinity;
    for(let i=0;i<m;i++)edge(src,i,a[i],0);
    for(let j=0;j<k;j++)edge(m+j,sink,b[j],0);
    let remaining=a.reduce((l,r)=>l+r,0);
    while(remaining--) {
      const d=Array(size).fill(Infinity), prev=Array(size), stack=[src], queued=Array(size).fill(false);
      d[src]=0;queued[src]=true;
      for(let h=0;h<stack.length;h++) {
        const u=stack[h];queued[u]=false;
        for(const e of g[u]) if(e.capacity>0 && d[e.v]>d[u]+e.cost) {
          d[e.v]=d[u]+e.cost;prev[e.v]=e;
          if(!queued[e.v]) { stack.push(e.v);queued[e.v]=true; }
        }
      }
      if(d[sink]===Infinity) return Infinity;
      ans+=d[sink];
      for(let v=sink;v!==src;v=prev[v].back.v) {
        prev[v].capacity--;prev[v].back.capacity++;
      }
    }
    return ans;
  }
  return ps.map((p,i)=>ps.map((q,j)=>j<i?null:min(p,q)));
}
function exam(n,d3,maximumDegree=n-14) {
  const ps=profiles(n,maximumDegree), allcost=costs(n,ps,d3), req=C(n), survivors=[];
  let total=0, min=Infinity;
  function go(start, chosen, totalS, totalT, totalCost) {
    if(chosen.length===6) {
      if(totalS<req)return;
      total++;
      const residual=totalS-req;
      min=Math.min(min,totalCost-2*residual);
      if(totalCost<=2*residual) survivors.push([chosen.map(i=>ps[i].p),totalS,totalT,totalCost]);
      return;
    }
    for(let i=start;i<ps.length;i++) {
      if(totalS+(6-chosen.length)*ps[i].s<req)break;
      if(totalT+ps[i].t>Math.floor(n/2))continue;
      go(i,chosen.concat(i),totalS+ps[i].s,totalT+ps[i].t,totalCost+chosen.reduce((a,j)=>a+allcost[j][i],0));
    }
  }
  go(0, [], 0, 0, 0);
  return {n,profiles:ps.length,total,min,survivors,ps,allcost};
}

return { exam, costs };
})();
const scan = (() => {

function scan(n, systems){
const C=d=>d*(d-1)/2, cache=new Map();
function options(p,q,d,istr){
 const key=[p,q,d,istr].join("|"); if(cache.has(key)) return cache.get(key);
 const m=n-d, list=[], limits=[m-9,m-5,m-3,m-1], a=[];
 function walk(j,rem){
    if(j===q.length){
      if(rem)return;
      const ds=q.map((v,i)=>v-a[i]).sort((a,b)=>b-a);
      if(limits.some((lim,k)=>ds.slice(0,k+1).reduce((a,b)=>a+b,0)>lim))return;
      const S=ds.reduce((a,b)=>a+C(b),0);
      const one=ds.filter(x=>x===1).length;
      const vstar=q.reduce((x,v,i)=>x+(v-a[i]===1?a[i]:0),0);
      const X=q.reduce((x,v,i)=>x+a[i]*(v-a[i]),0);
      list.push([S,one,vstar,X]); return;
    }
    const qj=q[j];
    const lo=Math.max(0,d+qj-(n-9));
    const hi=Math.min(rem,d===2||qj===2?(d===qj?0:1):istr&&(d===3||qj===3)?1:Math.min(d,qj)-1);
    for(let x=lo;x<=hi;x++){a[j]=x;walk(j+1,rem-x);}
 }
 walk(0,d);
 const squared=new Map();
 for(const [s,j,v,x] of list) {
   const t=[j,v,s]; const ky=t.join("/");
   if(!squared.has(ky)||squared.get(ky)[3]<x)squared.set(ky,[s,j,v,x]);
 }
 const res=[...squared.values()];
 cache.set(key,res);return res;
}
function vertex(p,i,d,istr) {
 const m=n-d;
 const q=p[i].slice(), j=q.indexOf(d);q.splice(j,1);
 const cuts=[m-9,m-5,m-3,m-1];
 if(cuts.some((c,k)=>q.slice(0,k+1).reduce((a,b)=>a+b,0)>c))return 1;
 const s=q.reduce((a,b)=>a+C(b),0);
 let states=new Map([[0,[0,0,s,0]]]);
 for(let k=0;k<6;k++) {
   if(k===i)continue;
   const dis=options(p[i],p[k],d,istr);
   if(!dis.length)return 2;
   const next=new Map();
   for(const [aa,bb,cc,dd] of states.values()) for(const [sc,one,star,cr] of dis){
     const j=aa+one,v=bb+star,s=cc+sc,x=dd+cr;
     if(j>m||v>d) continue;
     const key=[j,v,s].join(',');
     if(!next.has(key)||next.get(key)[3]<x)next.set(key,[j,v,s,x]);
   }
   if(!next.size)return 3;
   states=next;
 }
 return [...states.values()].some(x=>x[2]>=C(n-d)&&x[3]>=d*(n-d))?0:4;
}
const kept=[],stats=Array(5).fill(0);
for(const [p,s,t,l] of systems){
 let code=0;
 for(let i=0;i<6 && !code;i++) if(p[i][0]>=8)code=vertex(p,i,p[i][0],2*t>=n-1);
 stats[code]++;
 if(!code)kept.push([p,s,t,l]);
}
return {stats,kept,cache:cache.size};
}

return scan;
})();
const scanWithCollisionGap = (() => {

function scan(n, systems, cost){
const maxGap=systems.reduce((bound,[,s,,base])=>Math.max(bound,2*(s-n*(n-1)/2)-base),-Infinity);
const C=d=>d*(d-1)/2, cache=new Map();
function options(p,q,d,istr){
 const key=[p,q,d,istr].join("|"); if(cache.has(key)) return cache.get(key);

 const m=n-d, list=[], limits=[m-9,m-5,m-3,m-1], a=[];
 const id=p.indexOf(d), ps=p.filter((_,i)=>i!==id);
 const low=ps.map(x=>q.map(y=>Math.max(0,x+y-(n-9))));
 const high=ps.map(x=>q.map(y=>x===2||y===2?(x===y?0:1):istr&&(x===3||y===3)?1:Math.min(x,y)-1));
 const rowMin=(target,low,high)=>{
    const remaining=target-low.reduce((a,b)=>a+b,0);
    if(remaining<0)return Infinity;
    const inc=[];
    let val=0;
    for(let i=0;i<low.length;i++) {
      if(low[i]>high[i])return Infinity;
      val+=C(low[i]);
      for(let k=low[i];k<high[i];k++)inc.push(k);
    }
    if(remaining>inc.length)return Infinity;
    inc.sort((a,b)=>a-b);
    return val+inc.slice(0,remaining).reduce((a,b)=>a+b,0);
 };
 const baseline=cost(p,q,istr);
 if(!Number.isFinite(baseline))return [];

 function walk(j,rem){
    if(j===q.length){
      if(rem)return;
      const ds=q.map((v,i)=>v-a[i]).sort((a,b)=>b-a);
      if(limits.some((lim,k)=>ds.slice(0,k+1).reduce((a,b)=>a+b,0)>lim))return;
      const S=ds.reduce((a,b)=>a+C(b),0);
      const one=ds.filter(x=>x===1).length;
      const vstar=q.reduce((x,v,i)=>x+(v-a[i]===1?a[i]:0),0);
      const X=q.reduce((x,v,i)=>x+a[i]*(v-a[i]),0);

      const res=q.map((x,i)=>x-a[i]);
      const row=ps.reduce((s,x,i)=>s+rowMin(x,low[i],high[i].map((u,j)=>Math.min(u,res[j]))),0);
      const col=res.reduce((s,x,j)=>s+rowMin(x,low.map(r=>r[j]),high.map((u,i)=>Math.min(u[j],ps[i]))),0);
      const l=Math.max(0,Math.max(row,col)+a.reduce((e,x)=>e+C(x),0)-baseline);
      if(l<=maxGap)list.push([S,one,vstar,X,l]); return;
    }
    const qj=q[j];
    const lo=Math.max(0,d+qj-(n-9));
    const hi=Math.min(rem,d===2||qj===2?(d===qj?0:1):istr&&(d===3||qj===3)?1:Math.min(d,qj)-1);
    for(let x=lo;x<=hi;x++){a[j]=x;walk(j+1,rem-x);}
 }
 walk(0,d);
 const squared=new Map();
 for(const [s,j,v,x,l] of list) {
   const t=[j,v,s,l]; const ky=t.join("/");
   if(!squared.has(ky)||squared.get(ky)[3]<x)squared.set(ky,[s,j,v,x,l]);
 }
 const res=[...squared.values()];
 cache.set(key,res);return res;
}
function vertex(p,i,d,istr,slack) {
 const m=n-d;
 const q=p[i].slice(), j=q.indexOf(d);q.splice(j,1);
 const cuts=[m-9,m-5,m-3,m-1];
 if(cuts.some((c,k)=>q.slice(0,k+1).reduce((a,b)=>a+b,0)>c))return 1;
 const s=q.reduce((a,b)=>a+C(b),0);
 let states=new Map([[0,[0,0,s,0,0]]]);
 for(let k=0;k<6;k++) {
   if(k===i)continue;
   const dis=options(p[i],p[k],d,istr);
   if(!dis.length)return 2;
   const next=new Map();
   for(const [aa,bb,cc,dd,ee] of states.values()) for(const [sc,one,star,cr,l] of dis){
     const j=aa+one,v=bb+star,s=cc+sc,x=dd+cr;
     if(j>m||v>d||ee+l>slack) continue;
     const key=[j,v,s,ee+l].join(',');
     if(!next.has(key)||next.get(key)[3]<x)next.set(key,[j,v,s,x,ee+l]);
   }
   if(!next.size)return 3;
   states=next;
 }
 return [...states.values()].some(x=>x[2]>=C(n-d)&&x[3]>=d*(n-d))?0:4;
}
const kept=[],stats=Array(5).fill(0);
for(const [p,s,t,l] of systems){
 let code=0;
 for(let i=0;i<6 && !code;i++) if(p[i][0]>=7)code=vertex(p,i,p[i][0],2*t>=n-1,2*(s-C(n))-l);
 stats[code]++;
 if(!code)kept.push([p,s,t,l]);
}
return {stats,kept,cache:cache.size};
}

return scan;
})();
module.exports = {exam, costs, scan, scanWithCollisionGap};

function main() {
const n = 23;
const relaxed = exam(n, false);
const refined = new Set(exam(n, true).survivors.map(x => JSON.stringify(x[0])));
const first = relaxed.survivors.filter(x => 2*x[2]<n-1 || refined.has(JSON.stringify(x[0])));
const star = scan(n, first);
const profiles = [...new Set(star.kept.flatMap(([p]) => p.map(q => String(q))))].map(s => ({p: s.split(",").map(Number)}));
const ids = new Map(profiles.map((q,i) => [String(q.p), i]));
const tables = [costs(n, profiles, false), costs(n, profiles, true)];
function cost(p, q, strict) {
  const a = ids.get(String(p)), b = ids.get(String(q));
  return tables[Number(strict)][Math.min(a,b)][Math.max(a,b)];
}
const gap = scanWithCollisionGap(n, star.kept, cost);
const counts = [relaxed.profiles, relaxed.total, relaxed.survivors.length, first.length, star.kept.length, gap.kept.length];
console.log("h23 profile pipeline", counts.join(" "));
if (counts.join(",") !== "87,1756829,9614,5527,537,126") throw new Error("unexpected profile counts");
const target = process.argv[2] || path.join(__dirname, "systems-126.json");
fs.writeFileSync(target, JSON.stringify(gap.kept) + "\n");
}

if (require.main === module) main();
