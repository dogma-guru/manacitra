from pathlib import Path
import sys,itertools,json,time
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from scipy.special import gammaln,logsumexp
from hmm_model import fb,fit_job,simulate_span
rng=np.random.default_rng(40118001)
n=np.array([[0,1,2,1],[2,1,0,1]],dtype=np.float64);R=np.array([2.,2.]);q=np.array([[.2,.8],[.75,.35]]);u,d=.12,.21
ll,g,xi,le=fb(n,R,q,u,d);vals=[];paths=list(itertools.product([0,1],repeat=4));p=np.array([[1-u,u],[d,1-d]])
for path in paths:
    vals.append(np.log([d/(u+d),u/(u+d)][path[0]])+sum(le[t,path[t]] for t in range(4))+sum(np.log(p[path[t-1],path[t]]) for t in range(1,4)))
z=logsumexp(vals);post=np.exp(np.array(vals)-z)@np.array(paths);assert abs(z-ll)<1e-11;assert np.max(abs(post-g))<1e-12
span={'id':'synthetic','n':np.zeros((2,1000)),'R':[49,49],'record_c':1};true={'u':.07,'d':.14};sim=simulate_span(span,true,[.72,.92],[.3,.08],rng)
t=time.perf_counter();fit=fit_job([sim]);elapsed=time.perf_counter()-t
out={'seed':40118001,'enumeration_loglik_difference':float(ll-z),'posterior_max_difference':float(np.max(abs(post-g))),'synthetic_true':true,'synthetic_fit':fit,'seconds':elapsed}
(Path(__file__).resolve().parent/'hmm-numerics.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k!='synthetic_fit'}));print({k:fit['spans'][0][k] for k in ('b','ell','u','d')})
