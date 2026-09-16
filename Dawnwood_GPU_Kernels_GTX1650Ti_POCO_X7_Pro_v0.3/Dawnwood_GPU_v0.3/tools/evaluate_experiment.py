"""Compare supplied detector counts with supplied candidate/reference predictions.

No experimental data are generated or inferred. CSV columns: x,count (observed),
x,expected_count (predictions). All three files must use identical x values.
"""
from pathlib import Path
import argparse,csv,json,math

def read(path,column):
    with path.open(newline='') as f:rows=list(csv.DictReader(f))
    result=[(float(r['x']),float(r[column])) for r in rows]
    if not result or any(not math.isfinite(x) or not math.isfinite(y) or y<0 for x,y in result):raise ValueError('Finite positions and nonnegative counts are required')
    return result

def deviance(obs,pred):
    total=0.
    for (_,n),(_,mu) in zip(obs,pred):
        if mu==0:
            if n>0:return {'poisson_deviance':None,'infinite':True}
        else:total+=2*(mu-n+(n*math.log(n/mu) if n else 0))
    return {'poisson_deviance':total,'infinite':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--observed',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    obs=read(a.observed,'count');candidate=read(a.candidate,'expected_count');reference=read(a.reference,'expected_count')
    if [x for x,_ in obs]!=[x for x,_ in candidate] or [x for x,_ in obs]!=[x for x,_ in reference]:raise ValueError('Prediction files must match all observed x positions exactly')
    result={'observations':len(obs),'candidate':deviance(obs,candidate),'reference':deviance(obs,reference),'interpretation':'Descriptive fit scores only. Calibration, independence, uncertainty and model-selection design are supplied by the experiment, not this utility.'}
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
