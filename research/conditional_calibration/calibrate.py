"""Synthetic coverage stress tests; no model outputs, datasets or training.
Requires numpy 1.26.4 (version used for saved results). Never changes pilot code.
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import platform
import time
from datetime import datetime, timezone
import numpy as np

OUT=Path(__file__).resolve().parent
CASES=('symmetric_null','correlated_gain','asymmetric_null','rare_gain','random_seeds','random_authors')
N_VALUES=(30,120,300)
S=3
REPETITIONS=250
BOOTSTRAPS=10000
DATA_SEED=20261011
BOOT_SEED=101

def hoeffding_radius(weights, alpha=.05):
    w=np.asarray(weights,dtype=float)
    if w.ndim!=1 or np.any(w<0) or not np.isclose(w.sum(),1) or not 0<alpha<1:
        raise ValueError('Normalized nonnegative fixed weights and alpha in (0,1) required')
    return math.sqrt(2*math.log(2/alpha)*float(w@w))

def wilson(successes,n,z=1.959963984540054):
    p=successes/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den
    radius=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return max(0.,center-radius),min(1.,center+radius)

def bootstrap_interval(d,rng,b=BOOTSTRAPS):
    """Resample complete 3-seed family vectors for the mean contrast.
    Histogram of row sums is sufficient ONLY for this unweighted scalar mean.
    This compression is not a multivariate bootstrap or author-stratified method.
    """
    d=np.asarray(d)
    if d.ndim!=2 or d.shape[0]==0 or d.shape[1]!=S or not np.isin(d,[-1,0,1]).all() or b<1:
        raise ValueError('Require complete N x 3 paired correctness differences')
    sums=d.sum(axis=1)
    support,counts=np.unique(sums,return_counts=True)
    draws=rng.multinomial(len(d),counts/len(d),size=b)
    means=draws@support/(len(d)*S)
    lo,hi=np.quantile(means,[.025,.975],method='linear')
    return float(lo),float(hi),bool(len(support)==1)

def generate(case,n,rng):
    """Return valid pair-difference array and two explicitly distinct targets.
    Each difference can be realized as paired binary predictions. We need no
    arbitrary concordant-correct allocation to simulate this contrast.
    """
    if case=='asymmetric_null':
        positive=rng.random(n)<.25
        d=np.full((n,S),0,dtype=int)
        d[positive]=1
        negatives=np.flatnonzero(~positive)
        d[negatives,rng.integers(S,size=len(negatives))]=-1
        return d,0.,0.
    if case=='rare_gain':
        values=(rng.random(n)<.003).astype(int)
        return np.repeat(values[:,None],S,axis=1),.003,.003
    delta=0. if case=='symmetric_null' else .05
    seed_offsets=rng.choice([-.08,.08],S) if case=='random_seeds' else np.zeros(S)
    author_offsets=rng.choice([-.08,.08],3) if case=='random_authors' else np.zeros(3)
    author_index=np.arange(n)%3
    ds=delta+seed_offsets[None,:]+author_offsets[author_index,None]
    ds=np.broadcast_to(ds,(n,S))
    q=.20
    assert np.max(np.abs(ds))<=q
    # 70% of family rows share a uniform across seeds: within-family dependence.
    u=rng.random((n,S)); shared=rng.random(n)<.70
    u[shared]=u[shared,:1]
    pplus=(q+ds)/2
    d=np.where(u<pplus,1,np.where(u<q,-1,0))
    conditional=float(ds.mean())
    return d,conditional,delta

def validate():
    checks=[]
    rng=np.random.default_rng(99)
    for case in CASES:
        d,conditional,pop=generate(case,120,rng)
        assert d.shape==(120,3) and np.isin(d,[-1,0,1]).all()
        # Explicitly realize each entry as paired binary correctness.
        a=(d==1).astype(int);b=(d==-1).astype(int)
        assert np.array_equal(a-b,d)
    checks.append('All generators yield realizable paired binary differences')
    d=np.zeros((30,3),dtype=int)
    assert bootstrap_interval(d,rng)==(0.,0.,True)
    assert hoeffding_radius(np.ones(30)/30)>0
    checks.append('Zero sample gives degenerate bootstrap but nonzero bounded reference')
    d=np.array([[1,1,1],[-1,0,0],[0,-1,0],[0,0,-1]])
    assert d.mean()==0 and not np.allclose(np.sort(d.mean(axis=1)),np.sort(-d.mean(axis=1)))
    checks.append('Asymmetric weak-null construction has exact zero population mean')
    # Enumerate every ordered resample for a two-family case, independently.
    d=np.array([[1,1,1],[-1,-1,-1]])
    brute=np.array([d[list(x)].mean() for x in [(0,0),(0,1),(1,0),(1,1)]])
    assert np.array_equal(np.sort(brute),[-1,0,0,1])
    counts=np.array([[2,0],[1,1],[0,2]])
    compressed=counts@np.array([-3,3])/6
    assert np.array_equal(compressed,[-1,0,1])
    # Empirical resampling agrees with exact mean/variance of bootstrap mean.
    n=12;d=np.random.default_rng(17).choice([-1,0,1],size=(n,S))
    support,c=np.unique(d.sum(1),return_counts=True)
    draws=rng.multinomial(n,c/n,size=100000)@support/(n*S)
    assert abs(draws.mean()-d.mean())<.005
    assert abs(draws.var()-d.mean(1).var()/n)<.001
    checks.append('Histogram resampling matches explicit enumeration and mean/variance identities')
    assert abs(hoeffding_radius([.5,.5])-math.sqrt(math.log(40)))<1e-12
    try:hoeffding_radius([.2,.2])
    except ValueError:pass
    else:raise AssertionError('Unnormalized weights accepted')
    try:bootstrap_interval(np.zeros((5,2)),rng)
    except ValueError:pass
    else:raise AssertionError('Wrong seed shape accepted')
    assert wilson(0,250)[1]>0 and wilson(250,250)[0]<1
    checks.append('Weight and shape guards; bounded interval formula and Monte Carlo Wilson boundaries checked')
    return checks

def run():
    started=time.monotonic();checks=validate();rows=[]
    for k,case in enumerate(CASES):
        for n in N_VALUES:
            data_rng=np.random.default_rng(np.random.SeedSequence([DATA_SEED,k,n]))
            boot_rng=np.random.default_rng(np.random.SeedSequence([BOOT_SEED,k,n]))
            cover_fixed=cover_broad=bound_fixed=bound_broad=zero_width=positive=negative=0
            widths=[];estimates=[];targets=[]
            radius=hoeffding_radius(np.ones(n)/n)
            for _ in range(REPETITIONS):
                d,target,broad=generate(case,n,data_rng)
                lo,hi,degenerate=bootstrap_interval(d,boot_rng)
                estimate=float(d.mean());blo=max(-1,estimate-radius);bhi=min(1,estimate+radius)
                cover_fixed+=lo-1e-12<=target<=hi+1e-12
                cover_broad+=lo-1e-12<=broad<=hi+1e-12
                bound_fixed+=blo<=target<=bhi
                bound_broad+=blo<=broad<=bhi
                zero_width+=degenerate;positive+=lo>0;negative+=hi<0
                widths.append(hi-lo);estimates.append(estimate);targets.append(target)
            rate=cover_fixed/REPETITIONS
            mc_lo,mc_hi=wilson(cover_fixed,REPETITIONS)
            broad_lo,broad_hi=wilson(cover_broad,REPETITIONS)
            rows.append(dict(case=case,N=n,S=S,datasets=REPETITIONS,bootstrap_resamples=BOOTSTRAPS,
                bootstrap_coverage_fixed_realized_seeds_authors=rate,
                MCSE_fixed_coverage=math.sqrt(rate*(1-rate)/REPETITIONS),
                MC_Wilson_low_fixed=mc_lo,MC_Wilson_high_fixed=mc_hi,
                MC_Wilson_low_broader=broad_lo,MC_Wilson_high_broader=broad_hi,
                bootstrap_coverage_broader_target=cover_broad/REPETITIONS,
                bounded_coverage_fixed=bound_fixed/REPETITIONS,
                bounded_coverage_broader=bound_broad/REPETITIONS,
                degenerate_rate=zero_width/REPETITIONS,positive_interval_rate=positive/REPETITIONS,negative_interval_rate=negative/REPETITIONS,
                median_interval_width=float(np.median(widths)),p95_interval_width=float(np.quantile(widths,.95)),
                mean_interval_width=float(np.mean(widths)),mean_estimate=float(np.mean(estimates)),
                mean_conditional_target=float(np.mean(targets)),hoeffding_radius=radius))
            print(case,n,'conditional coverage',round(rate,3),'broader',round(cover_broad/REPETITIONS,3),flush=True)
    path=OUT/'synthetic_coverage.csv'
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    manifest=dict(status='SYNTHETIC_DESIGN_CALIBRATION_NOT_RESEARCH_EVIDENCE',created_utc=datetime.now(timezone.utc).isoformat(),
        python=platform.python_version(),numpy=np.__version__,code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        outputs={path.name:hashlib.sha256(path.read_bytes()).hexdigest()},data_seed=DATA_SEED,bootstrap_seed=BOOT_SEED,
        seed_derivation='numpy SeedSequence([master_seed,case_index,N]); sequential replicates',
        repetitions=REPETITIONS,bootstrap_resamples=BOOTSTRAPS,cases=list(CASES),N_values=list(N_VALUES),checks=checks,
        elapsed_seconds=time.monotonic()-started,
        limitations=['No real model results or family data used.','250 datasets per cell is a screening calibration with Monte Carlo uncertainty.',
        'Broader-target coverage is intentionally misspecified when seeds/authors are random; bounded family formula has no broader-target guarantee.',
        'Fixed-author conditional coverage assumes independent families given realized author effects; broader author inference requires an author sampling design.',
        'Conditional coverage for random_seeds/authors is averaged across newly realized offsets, not uniform or one-fixed-parameter conditional coverage.',
        'Author case uses pooled family resampling, not stratified conditional-author or author-block resampling.',
        'Does not calibrate topic stratification, general author heterogeneity, formal p-values, or every real data distribution.'])
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('PASS',len(rows),'scenarios;',len(checks),'validation categories;',round(manifest['elapsed_seconds'],2),'seconds')

if __name__=='__main__':run()
