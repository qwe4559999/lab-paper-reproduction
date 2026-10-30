"""Check a numeric 8-column PeakFit Origin export; no fitting or data mutation."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np

def check(path):
    rows=[]; observed_only=[]; malformed=[]
    for line_no,line in enumerate(path.read_text(encoding='utf-8-sig',errors='replace').splitlines(),1):
        tokens=line.split()
        if not tokens:continue
        try:values=[float(v) for v in tokens]
        except ValueError:
            try:float(tokens[0])
            except ValueError:continue
            malformed.append({'line':line_no,'numeric_columns':len(tokens),'reason':'numeric-leading row contains nonnumeric token'})
            continue
        if len(values)==8:rows.append(values)
        elif len(values)==2:observed_only.append(values)
        else:malformed.append({'line':line_no,'numeric_columns':len(values)})
    a=np.asarray(rows,dtype=float)
    if a.ndim!=2 or a.shape[1]!=8 or not len(a):raise ValueError('No eight-column numeric rows')
    valid=np.isfinite(a[:,2:]).all(axis=1); g=a[valid]
    if not len(g):raise ValueError('No finite generated rows')
    error=np.max(np.abs(g[:,4:8].sum(axis=1)-g[:,3]))
    tolerance=1e-8*max(1.,float(np.max(np.abs(g[:,3]))))
    obs=np.vstack([a[:,:2],np.asarray(observed_only).reshape(-1,2)])
    paired=np.isfinite(a[:,:3]).all(axis=1)
    x_difference=float(np.max(abs(a[paired,0]-a[paired,2]))) if paired.any() else None
    integrity=bool(np.isfinite(obs).all() and valid.all() and not malformed)
    return dict(file=str(path.resolve()),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),numeric_rows=len(a)+len(observed_only),observed_rows=len(obs),eight_column_rows=len(a),observed_only_two_column_rows=len(observed_only),finite_generated_rows=len(g),nonfinite_observed_rows=int(np.sum(~np.isfinite(obs).all(axis=1))),nonfinite_generated_rows=int(np.sum(~valid)),malformed_numeric_rows=malformed,input_integrity_pass=integrity,component_sum_max_abs_error=float(error),sum_tolerance=tolerance,component_sum_pass=bool(error<=tolerance),max_rowwise_observed_generated_x_difference=x_difference,rowwise_residual_safe=bool(integrity and not observed_only and np.allclose(a[:,0],a[:,2],rtol=0,atol=1e-8)),observed_x_non_increasing_steps=int(np.sum(np.diff(obs[:,0])<=0)),generated_x_non_increasing_steps=int(np.sum(np.diff(g[:,2])<=0)),component_identity='Peak1-4; S1-4 mapping requires author report',fit_quality='not assessed; no residual or R2 inferred from rowwise arrays')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('files',nargs='+',type=Path);p.add_argument('--out',type=Path);args=p.parse_args()
    results=[check(f) for f in args.files]
    result=json.dumps(results,ensure_ascii=False,indent=2)
    if args.out:args.out.write_text(result,encoding='utf8')
    else:print(result)
    if not all(r['component_sum_pass'] and r['input_integrity_pass'] for r in results):raise SystemExit(1)
