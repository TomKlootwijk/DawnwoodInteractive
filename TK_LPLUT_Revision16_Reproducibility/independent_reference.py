#!/usr/bin/env python3
"""Revision 16 independent arithmetic reference.

Reconstructs selected equations and literal vectors from the supplied Revision 15
PDF. This is NOT the solvefinite implementation, its regression suite, a GPU test,
or a validation of physical claims. The optional phase-window checks concern the
new FORMAL-ONLY extension, not a deployed kernel feature.

Run: python independent_reference.py --output independent_checks.json
Only the Python standard library is required. Assertions raise on disagreement.
"""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
import heapq
import itertools
import json
import math
from pathlib import Path
import platform
import sys
import time
from typing import Iterable

STEP, DATA, EMIT = 1, 0, 6
MASK = (1 << 32) - 1
REPORT: list[dict] = []

def integer(x: int, lo: int, hi: int) -> None:
    if type(x) is not int or not lo <= x <= hi:
        raise ValueError(f'not a strict integer in [{lo},{hi}]: {x!r}')

def pack(r: int, g: int, b: int, a: int) -> int:
    integer(r, 0, 255); integer(g, 0, 255)
    integer(b, -128, 127); integer(a, 0, 127)
    raw = r | (g << 8) | ((b & 255) << 16) | (a << 24)
    return raw | ((raw.bit_count() & 1) << 31)

def unpack(w: int) -> tuple[int, int, int, int]:
    integer(w, 0, MASK)
    if w.bit_count() & 1:
        raise ValueError('invalid parity')
    b = (w >> 16) & 255
    return w & 255, (w >> 8) & 255, b - 256 if b >= 128 else b, (w >> 24) & 127

def mirror(w: int) -> int:
    r,g,b,a = unpack(w)
    return pack((-r) & 255, g, b, a ^ 16)

def pair(w: int) -> int:
    return w | (mirror(w) << 32)

def valid_pair(p: int) -> bool:
    try:
        integer(p,0,(1<<64)-1)
        unpack(p & MASK); unpack(p >> 32)
        return mirror(p & MASK) == p >> 32
    except ValueError:
        return False

def phase(r: int, eta: int) -> int:
    return (-r if eta else r) & 255

def transport(r: int, eta: int, delta: int, tau: int) -> tuple[int,int]:
    v = (r + (-delta if eta else delta)) & 255
    return ((-v if tau else v) & 255, eta ^ tau)

def advance_word(w: int, delta: int, dest: int, b: int, tau: int=0) -> int:
    r,_,_,a = unpack(w)
    rr,ee = transport(r, (a >> 4) & 1, delta, tau)
    return pack(rr,dest,b,STEP | (ee<<4))

def mark(name: str, cases: int, source: str, details: dict | None=None) -> None:
    REPORT.append({'name':name,'status':'PASS','cases':cases,'source':source,'details':details or {}})

def bfs(adj: list[list[int]], sources: Iterable[int]) -> list[int]:
    ds=[-1]*len(adj); q=deque()
    for i in sources:
        if ds[i] < 0: ds[i]=0; q.append(i)
    if not q: raise ValueError('empty boundary')
    while q:
        u=q.popleft()
        for v in adj[u]:
            if ds[v] < 0: ds[v]=ds[u]+1; q.append(v)
    if min(ds)<0: raise ValueError('disconnected graph')
    return ds

class Klein:
    def __init__(self,w: int,h: int,d: int|None=None):
        self.w=w; self.h=h; self.d=d; self.n=w*h*(d or 1)
        self.directions=((1,0),(0,1),(-1,0),(0,-1)) if d is None else ((1,0,0),(0,1,0),(0,0,1),(-1,0,0),(0,-1,0),(0,0,-1))
        self.coords=list(itertools.product(range(w),range(h))) if d is None else list(itertools.product(range(w),range(h),range(d)))
        self.slots=[]
        for p in self.coords:
            self.slots.append([self.project(tuple(x+y for x,y in zip(p,e))) for e in self.directions])
        self.adj=[sorted(set(row)) for row in self.slots]
    def project(self,p: tuple[int,...]) -> int:
        x,y=p[:2]; k=x//self.w; u=x-k*self.w; v=((-1 if k&1 else 1)*y)%self.h
        return u*self.h+v if self.d is None else (u*self.h+v)*self.d+p[2]%self.d
    def seam(self,i: int,j: int) -> int:
        return int(abs(self.coords[i][0]-self.coords[j][0])==self.w-1)
    def name(self,i: int) -> str:
        return ('k:' if self.d is None else 'v:')+':'.join(map(str,self.coords[i]))

def signed_field(adj: list[list[int]], signs: list[int]) -> list[int]:
    z=[i for i,s in enumerate(signs) if s==0]
    ds=bfs(adj,z)
    values=[s*d for s,d in zip(signs,ds)]
    if not certificate(adj,signs,values): raise ValueError('failed certificate')
    return values

def certificate(adj: list[list[int]], signs: list[int], f: list[int]) -> bool:
    if len(f)!=len(adj) or len(signs)!=len(adj) or 0 not in signs: return False
    for i,v in enumerate(f):
        if type(v) is not int or not -127<=v<=127 or signs[i] not in [-1,0,1]: return False
        if (v>0)-(v<0) != signs[i]: return False
        if any(signs[i]*signs[j]==-1 or abs(v-f[j])>1 for j in adj[i]): return False
        if v and not any(abs(v)==abs(f[j])+1 for j in adj[i]): return False
    return True

def ball_field(k: Klein, center: int, radius: int) -> list[int]:
    ds=bfs(k.adj,[center]); signs=[(v>radius)-(v<radius) for v in ds]
    return signed_field(k.adj,signs)

def occupancy_field(k: Klein, u: set[int]) -> tuple[set[int], list[int]]:
    if not u or len(u)==k.n: raise ValueError('empty/full occupied set')
    z={v for v in u if any(j not in u for j in k.adj[v])}
    signs=[0 if i in z else (-1 if i in u else 1) for i in range(k.n)]
    return z,signed_field(k.adj,signs)

def psi_at(k: Klein, f: list[int], i: int) -> tuple[tuple[int,...], tuple[int,...], int]:
    half=len(k.directions)//2
    g=tuple(f[k.slots[i][a]]-f[k.slots[i][a+half]] for a in range(half))
    div=math.gcd(*map(abs,g))
    psi=tuple(v//div for v in g) if div else tuple([1]+[0]*(half-1))
    return g,psi,sum(v*v for v in g)

GAINS=((1,1),(-1,1),(-1,-1),(1,-1))
def cost(k: Klein, f: list[int], i: int, t: int, j: int, hazard: int=0) -> int:
    g,p,_=psi_at(k,f,i)
    q=tuple(GAINS[t//64][a]*(1+p[a]*p[a])*g[a] for a in range(2))
    e=k.directions[k.slots[i].index(j)]
    penalty=max(map(abs,q))-sum(v*x for v,x in zip(q,e))
    assert 0<=penalty<=80
    return 1+abs(f[j])+hazard+penalty

def klass(v: int) -> int: return 0 if v<0 else (1 if v==0 else 2)

def shortest(k: Klein,f: list[int],src: int,dst: int,t0: int,hmax: int,omit_phase: bool=False):
    # Deliberately broken variant exists only for the retained counterexample.
    seed=(src,0) if omit_phase else (src,t0,0)
    best={seed:(0,())}; heap=[(0,(),src,t0,0,())]
    while heap:
        c,names,i,t,h,route=heapq.heappop(heap)
        key=(i,h) if omit_phase else (i,t,h)
        if best.get(key)!=(c,names): continue
        if i==dst: return list(route),c
        if h==hmax: continue
        for j in sorted(k.adj[i], key=k.name):
            tt=(t+(11,53,137)[klass(f[i])])&255
            cc=c+cost(k,f,i,t,j); nn=names+(k.name(j),); rr=route+(j,)
            kk=(j,h+1) if omit_phase else (j,tt,h+1)
            if kk not in best or (cc,nn)<best[kk]:
                best[kk]=(cc,nn); heapq.heappush(heap,(cc,nn,j,tt,h+1,rr))
    raise ValueError('no route')

def run_checks() -> None:
    # A. Exact carrier, lane boundaries, mirror, and bit-detection examples.
    tuples=[]
    for axis,(lo,hi) in enumerate(((0,255),(0,255),(-128,127),(0,127))):
        for v in range(lo,hi+1):
            a=[250,3,-7,1]; a[axis]=v; tuples.append(tuple(a))
    for a in tuples:
        w=pack(*a); assert unpack(w)==a and mirror(mirror(w))==w and valid_pair(pair(w))
    mark('RP32 lane sweeps and mirror involution',len(tuples),'K pp.7-8')
    seed=pack(250,3,-7,STEP); words=[seed]
    for delta in (11,9): words.append(advance_word(words[-1],delta,3,-7))
    expected=['11F9030681F903FA','91F903FB81F90305','91F903F201F9030E']
    assert [f'{pair(w):016X}' for w in words]==expected
    mark('Three literal packed pairs',3,'K p.8',{'pairs':expected})
    count=0
    for p in [pair(w) for w in words]+[pair(pack(0,0,0,DATA))]:
        for bit in range(64): assert not valid_pair(p^(1<<bit)); count+=1
    assert pair(pack(0,0,0,DATA))==0x9000000000000000 and not valid_pair(0)
    assert pack(0,0,3,DATA)^pack(0,0,4,DATA)==0x80070000
    mark('Single-bit detection and typed-zero examples',count+3,'K p.24')

    # B. Exhaust the finite phase/increment/seam domain, using two views.
    count=0
    for r,eta,delta,tau in itertools.product(range(256),range(2),range(256),range(2)):
        rr,ee=transport(r,eta,delta,tau)
        mr,me=transport((-r)&255,eta^1,delta,tau)
        assert (mr,me)==((-rr)&255,ee^1)
        assert phase(rr,ee)==(phase(r,eta)+delta)&255
        assert 0<=rr<256 and ee in (0,1)
        count+=1
    mark('Exhaustive K8 phase and mirror coherence',count,'K pp.6,8,20; LP normal form')
    count=0
    for r,eta,d1,d2,t1,t2 in itertools.product(range(256),range(2),(0,1,11,53,137,255),(0,9,64,255),range(2),range(2)):
        a,b=transport(r,eta,d1,t1); a,b=transport(a,b,d2,t2)
        x,y=transport(r,eta,(d1+d2)&255,t1^t2)
        assert (a,b)==(x,y); count+=1
    mark('Two-pinion fixed-path phase normal form',count,'Derived from K pp.6,20')

    # C. Exact default scalar field and literal trace, with weighted edges.
    edges=[(0,1,2),(1,2,1),(2,3,3),(3,4,2),(4,5,1),(5,6,2)]
    dist=[10**9]*7; dist[3]=0; heap=[(0,3)]; adj=[[] for _ in range(7)]
    for i,j,w in edges: adj[i].append((j,w)); adj[j].append((i,w))
    while heap:
        d,i=heapq.heappop(heap)
        if d!=dist[i]: continue
        for j,w in adj[i]:
            if d+w<dist[j]: dist[j]=d+w; heapq.heappush(heap,(d+w,j))
    f=[s*d for s,d in zip([-1,-1,-1,0,1,1,1],dist)]
    assert f==[-6,-4,-3,0,2,3,5]
    routes=[[1,1,0],[2,2,0],[3,3,1],[4,4,2],[5,5,3],[6,6,4],[6,6,5]]
    w=pack(250,0,f[0],STEP)
    for _ in range(64):
        _,i,b,_=unpack(w); c=klass(b); j=routes[i][c]; w=advance_word(w,(11,53,137)[c],j,f[j])
    assert pair(w)==0x1102046C01020494
    mark('Weighted seven-node SDF and 64-tick v1 trace',65,'K pp.27,31',{'field':f,'final_pair':f'{pair(w):016X}'})
    k=Klein(8,8); f=ball_field(k,0,2); w=pack(250,0,f[0],STEP); seams=0
    for _ in range(64):
        _,i,b,_=unpack(w); j=k.slots[i][0]; tau=k.seam(i,j); seams+=tau
        w=advance_word(w,(11,53,137)[klass(b)],j,f[j],tau)
    assert pair(w)==0x11FE00D681FE002A and seams==8
    mark('Klein default 64-tick seam trace',64,'K p.21',{'seams':seams,'final_pair':f'{pair(w):016X}'})

    # D. Local eigenvectors and the actual middle-out key order.
    count=0
    for gu,gv,eps,frame in itertools.product(range(-2,3),range(-2,3),(-1,1),(-1,1)):
        g=(gu,gv); div=math.gcd(abs(gu),abs(gv)); p=(gu//div,gv//div) if div else (1,0)
        p=tuple(eps*x for x in p); lam=gu*gu+gv*gv
        assert tuple(x*sum(y*z for y,z in zip(g,p)) for x in g)==tuple(lam*x for x in p)
        gg=(gu,frame*gv); pp=(p[0],frame*p[1]); assert sum(x*x for x in gg)==lam
        assert tuple(x*sum(y*z for y,z in zip(gg,pp)) for x in gg)==tuple(lam*x for x in pp)
        count+=1
    mark('Local Psi, degeneracy and reflected frames',count,'K p.39')
    k=Klein(4,5); f=ball_field(k,0,2); ds=bfs(k.adj,[0]); ts=[0]*k.n
    for i in sorted(range(k.n),key=lambda i:ds[i]):
        if i: parent=min(j for j in k.adj[i] if ds[j]==ds[i]-1); ts[i]=(ts[parent]+(11,53,137)[klass(f[parent])])&255
    keys={i:(psi_at(k,f,i)[1][0]+2,psi_at(k,f,i)[1][1]+2,(ds[i]+1).bit_length()-1,ts[i],i) for i in range(k.n)}
    order=sorted(keys,key=keys.get)
    assert order==[18,17,19,15,16,4,3,14,13,1,2,11,12,9,0,5,10,6,8,7]
    def pre(a):
        if not a: return []
        m=(len(a)-1)//2
        return [a[m]]+pre(a[:m])+pre(a[m+1:])
    preorder=pre(order)
    assert preorder==[1,16,17,18,19,15,3,4,14,13,0,11,2,12,9,6,5,10,8,7]
    mark('PX canonical key and lower-median orders',20,'K pp.40-43',{'sorted':order,'preorder':preorder})
    w=pack(250,0,f[0],STEP); energy=100; got=[]
    routes=([4,3,17],[16,17],[17]); route_expected=(7,7,2)
    for route,expect in zip(routes,route_expected):
        r,i,b,a=unpack(w); t=phase(r,(a>>4)&1); total=0; u=i; tt=t
        for j in route:
            total+=cost(k,f,u,tt,j); tt=(tt+(11,53,137)[klass(f[u])])&255; u=j
        assert total==expect
        j=route[0]; energy-=cost(k,f,i,t,j); w=advance_word(w,(11,53,137)[klass(b)],j,f[j],k.seam(i,j)); got.append((f'{pair(w):016X}',energy))
    r,i,b,a=unpack(w); w=pack(r,i,b,EMIT|(a&16)); energy-=5; got.append((f'{pair(w):016X}',energy))
    assert got==[('11FF04FB01FF0405',98),('81001010910010F0',93),('81011145910111BB',91),('06011145160111BB',86)]
    mark('HP reference edge costs and owned pairs',4,'K p.48',{'actions':got})
    good=shortest(k,f,0,10,128,12); bad=shortest(k,f,0,10,128,12,True)
    assert good==([1,6,5,10],10) and bad==([5,10],11)
    mark('Phase-retaining versus phase-dropping search witness',2,'K p.48',{'phase_labels':good,'phase_free_labels':bad})

    # E. Preserve distinct field-construction profiles.
    k=Klein(3,3); a=bfs(k.adj,[0]); b=bfs(k.adj,[4]); q=[min(x-2,y-2) for x,y in zip(a,b)]
    signs=[(v>0)-(v<0) for v in q]; f=signed_field(k.adj,signs)
    assert q==[-2,-1,-1,-1,-2,-1,-1,-1,0] and f==[-2,-1,-2,-2,-2,-1,-1,-1,0]
    forged=f[:]; forged[2]=q[2]; assert not certificate(k.adj,signs,forged)
    mark('OG union-redistance and geometric forgery rejection',10,'K pp.14,61,65',{'margin':q,'field':f})
    k=Klein(8,8); u={k.project((1+s,3+t)) for s in range(4) for t in range(-s,s+1)}
    z,f=occupancy_field(k,u); inside={i for i,v in enumerate(f) if v<0}
    assert len(u)==16 and len(z)==12 and inside=={19,26,27,28}
    assert 38 in z and not any(f[j]<0 for j in k.adj[38])
    mark('DP taper distinguishes the OG field family',64,'K p.90',{'occupied':16,'boundary':12,'interior':sorted(inside),'witness':38})
    old=ball_field(Klein(3,5),1,3)[0]; new=ball_field(Klein(6,10),2,6)[0]
    assert (old,new)==(-3,-4)
    mark('GD redistance is not a shifted old B lane',2,'K p.51',{'old_B':old,'new_B':new})
    k=Klein(6,6,6); results={}
    for kind in ('cone','pyramid','sphere'):
        if kind=='sphere':
            u={k.project((3+x,3+y,3+z)) for x,y,z in itertools.product(range(-2,3),repeat=3) if x*x+y*y+z*z<=4}
        else:
            u=set()
            for s,t,r in itertools.product(range(5),range(-2,3),range(-2,3)):
                ok=4*(t*t+r*r)<=s*s if kind=='cone' else 2*max(abs(t),abs(r))<=s
                if ok: u.add(k.project((s,3+t,3+r)))
        z,ff=occupancy_field(k,u)
        cubes=sum(all(k.project((x+a,y+b,z0+c)) in u for a,b,c in itertools.product(range(2),repeat=3)) for x,y,z0 in k.coords)
        results[kind]=[len(u),len(z),len(u-z),cubes]
    assert results=={'cone':[29,27,2,4],'pyramid':[45,43,2,8],'sphere':[33,26,7,8]}
    mark('VP three-solid literal occupancy expectations',3,'K p.104; FORMAL ONLY baseline',results)
    def limbs_square(x):
        a=x&65535; b=x>>16; lo=a*a; cross=2*a*b+(lo>>16); upper=b*b+(cross>>16)
        assert lo<=MASK and cross<=MASK and upper<=MASK
        return [lo&65535,cross&65535,upper&65535,upper>>16]
    vals=list(range(65536))+[65536,65537,2**30-1,2**30,2**31-2,2**31-1]
    for x in vals: assert sum(v<<(16*i) for i,v in enumerate(limbs_square(x)))==x*x
    wrong=0
    for s,t,r in itertools.product(range(3),range(-2,3),range(-2,3)):
        exact=(65534*abs(t))**2+(65534*abs(r))**2<=(65535*s)**2
        wrapped=(((65534*abs(t))**2+(65534*abs(r))**2)&MASK)<=((65535*s)**2&MASK)
        wrong+=exact!=wrapped
    assert wrong==40
    mark('VP exact limbs and small-work u32 overflow witness',len(vals)+75,'K p.112; FORMAL ONLY baseline',{'wrapped_membership_disagreements':wrong,'charged_sites':75})

    # F. Fragmentation examples; no endpoint, journal, GPU or persistence claim.
    raw=bytes.fromhex('DEADBEEF0123456789')
    chunks=[int.from_bytes(raw[i:i+4].ljust(4,b'\0'),'little') for i in range(0,len(raw),4)]
    out=[(65531<<48)|(0xFA00<<32)|v for v in chunks]
    assert [f'{w:016X}' for w in out]==['FFFBFA00EFBEADDE','FFFBFA0067452301','FFFBFA0000000089']
    count=0
    for length in (0,1,5,9,4096):
        raw=bytes((i*37)&255 for i in range(length)); pieces=[int.from_bytes(raw[i:i+4].ljust(4,b'\0'),'little') for i in range(0,length,4)]
        rebuilt=b''.join(v.to_bytes(4,'little') for v in pieces)[:length]; assert rebuilt==raw; count+=1
    mark('W raw-fragment byte order and lengths',count+1,'K pp.73,80',{'literal_words':[f'{w:016X}' for w in out]})

    # G. New opt-in window algebra. Existing profiles have no added gate.
    count=0
    for start in range(256):
        deltas=[(t-start)&255 for t in range(256)]
        for length in range(257):
            assert sum(d<length for d in deltas)==length
            count+=1
    assert [t for t in range(256) if ((t-252)&255)<8]==[0,1,2,3,252,253,254,255]
    mark('Optional phase-window cardinality including wrap',count,'NEW LG formal-only extension',{'membership_evaluations':256*256*257,'wrapped_window':[252,253,254,255,0,1,2,3]})
    count=0
    for r,eta,a in itertools.product(range(256),range(2),range(256)):
        t=phase(r,eta); tm=phase((-r)&255,eta^1)
        assert (((t-a)&255)<8)==(((tm-a)&255)<8); count+=1
    mark('Optional phase-window full-mirror invariance',count,'NEW LG formal-only extension')

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,default=Path('independent_checks.json'))
    args=ap.parse_args(); start=time.perf_counter(); failure=None
    try: run_checks()
    except Exception as exc: failure=f'{type(exc).__name__}: {exc}'
    record={
        'format':'tk-lplut-rev16-independent-arithmetic-v1',
        'scope':'Independent CPU reference reconstructed from supplied PDFs; not solvefinite regression or GPU verification.',
        'baseline_status':'Historical runtime results are reported by Revision 15 and were not rerun here. VP remains formal only.',
        'new_extension_status':'LG is opt-in FORMAL ONLY; no production integration or W endpoint is claimed.',
        'python':platform.python_version(), 'platform':platform.platform(),
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'elapsed_seconds':round(time.perf_counter()-start,6),
        'named_groups_passed':len(REPORT),'failure':failure,'groups':REPORT}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'groups_passed':len(REPORT),'failure':failure,'elapsed_seconds':record['elapsed_seconds']},indent=2))
    return int(failure is not None)

if __name__=='__main__': sys.exit(main())
