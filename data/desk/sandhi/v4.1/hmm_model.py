"""Float64 exact stationary initial two state binomial hidden Markov likelihood."""
from pathlib import Path
import ctypes, os, subprocess
import numpy as np
from scipy.special import expit, logit, gammaln
from scipy.optimize import minimize

HERE=Path(__file__).resolve().parent
libpath=HERE/'hmm_core.dylib'
if not libpath.exists():
    subprocess.run(['cc','-O3','-shared','-fPIC',str(HERE/'hmm_core.c'),'-o',str(libpath)],check=True)
LIB=ctypes.CDLL(str(libpath)); P=ctypes.POINTER(ctypes.c_double); U=ctypes.POINTER(ctypes.c_ubyte)
LIB.hmm_fb.argtypes=[ctypes.c_int,P,ctypes.c_double,ctypes.c_double,P,P];LIB.hmm_fb.restype=ctypes.c_double
LIB.hmm_viterbi.argtypes=[ctypes.c_int,P,ctypes.c_double,ctypes.c_double,U]
LIB.hmm_path.argtypes=[ctypes.c_int,P,ctypes.c_double,ctypes.c_double,U]
def ptr(x):return x.ctypes.data_as(P)
def derived(u,d):
    rho=1-u-d
    return {'u':float(u),'d':float(d),'b':float(u/(u+d)),'rho':float(rho),'ell':float(-1/np.log(rho)) if 0<rho<1 else None,'mean_dwell_H':float(1/d),'mean_dwell_L':float(1/u),'ell_status':'finite positive' if 0<rho<1 else 'undefined real positive correlation length'}
def prep(s):
    n=np.asarray(s['n'],dtype=np.float64);R=np.asarray(s['R'],dtype=np.float64)
    return n,R,float(np.sum(gammaln(R[:,None]+1)-gammaln(n+1)-gammaln(R[:,None]-n+1)))
def logemit(n,R,q):return np.ascontiguousarray((n.T@np.log(q).T+(R[:,None]-n).T@np.log1p(-q).T),dtype=np.float64)
def fb(n,R,q,u,d):
    le=logemit(n,R,q);off=le.max(axis=1);e=np.ascontiguousarray(np.exp(le-off[:,None]));g=np.empty(n.shape[1],dtype=np.float64);xi=np.empty(4,dtype=np.float64)
    ll=LIB.hmm_fb(len(g),ptr(e),u,d,ptr(g),ptr(xi))+off.sum()
    return ll,g,xi,le
def init_params(spans):
    C=len(spans[0]['R']);qc=int(spans[0]['record_c']);sums=np.zeros((2,C));den=np.zeros((2,C));rates=[]
    for s in spans:
        n=np.asarray(s['n'],dtype=np.float64);R=np.asarray(s['R'],dtype=np.float64);m=n[qc]/R[qc];path=m>np.mean(np.quantile(m,[.1,.9]));
        for k in (0,1):sums[k]+=n[:,path==k].sum(axis=1);den[k]+=R*np.sum(path==k)
        u=(np.sum((~path[:-1])&path[1:])+.5)/(np.sum(~path[:-1])+1);d=(np.sum(path[:-1]&(~path[1:]))+.5)/(np.sum(path[:-1])+1);rates.append([u,d])
    return np.clip(sums/np.maximum(den,1),1e-4,1-1e-4),np.clip(rates,1e-4,1-1e-4)
def fit_job(spans,q_init=None,common_rates=False,starts=4,rate_init=None,positive_rho=False,return_series=True,maxiter=500):
    prepared=[prep(s) for s in spans];C=len(spans[0]['R']);K=len(spans);q0,r0=init_params(spans)
    if q_init is not None:q0=np.asarray(q_init,dtype=np.float64)
    if rate_init is not None:r0=np.asarray(rate_init,dtype=np.float64)
    if common_rates:r0=np.mean(r0,axis=0)[None,:]
    def encode(r):
        if positive_rho:return logit(np.clip(np.c_[r[:,0]/r.sum(axis=1),r.sum(axis=1)],1e-7,1-1e-7)).ravel()
        return logit(np.clip(r,1e-7,1-1e-7)).ravel()
    def decode(x):
        w=expit(x[2*C:]).reshape(-1,2)
        return np.c_[w[:,0]*w[:,1],(1-w[:,0])*w[:,1]] if positive_rho else w
    def objective(x):
        q=expit(x[:2*C]).reshape(2,C);rates=decode(x);gq=np.zeros_like(q);gr=np.zeros_like(rates);ll=0.
        for i,(n,R,const) in enumerate(prepared):
            r=0 if common_rates else i;u,d=rates[r];val,g,xi,_=fb(n,R,q,u,d);ll+=val+const
            weights=np.array([1-g,g]);gq+=weights@n.T-weights.sum(axis=1)[:,None]*R[None,:]*q
            gr[r,0]+=xi[1]/u-xi[0]/(1-u)+g[0]/u-1/(u+d)
            gr[r,1]+=xi[2]/d-xi[3]/(1-d)+(1-g[0])/d-1/(u+d)
        if positive_rho:
            w=expit(x[2*C:]).reshape(-1,2);b,s=w.T;grad_rates=np.c_[(gr[:,0]-gr[:,1])*s*b*(1-b),(gr[:,0]*b+gr[:,1]*(1-b))*s*(1-s)]
        else:grad_rates=gr*rates*(1-rates)
        return -ll,-np.r_[gq.ravel(),grad_rates.ravel()]
    best=None;attempts=[]
    for f in [1.,.35,2.,.08][:starts]:
        rr=np.clip(r0*f,1e-6,.999999);x=np.r_[logit(np.clip(q0,1e-7,1-1e-7)).ravel(),encode(rr)]
        res=minimize(objective,x,jac=True,method='L-BFGS-B',bounds=[(-16,16)]*len(x),options={'ftol':1e-12,'gtol':1e-6,'maxiter':maxiter,'maxls':30})
        attempts.append({'success':bool(res.success),'message':str(res.message),'iterations':int(res.nit),'loglik':float(-res.fun),'gradient_max':float(np.max(np.abs(res.jac)))})
        if best is None or res.fun<best.fun:best=res
    q=expit(best.x[:2*C]).reshape(2,C);rates=decode(best.x)
    if not best.success:
        retry=minimize(objective,best.x,jac=True,method='L-BFGS-B',bounds=[(-16,16)]*len(best.x),options={'ftol':1e-10,'gtol':1e-5,'maxiter':1000,'maxls':100})
        attempts.append({'success':bool(retry.success),'message':str(retry.message),'iterations':int(retry.nit),'loglik':float(-retry.fun),'gradient_max':float(np.max(np.abs(retry.jac))),'retry':'Stationary start with numerical convergence tolerances relaxed after line search failure'})
        if retry.success and retry.fun<=best.fun+1e-7:best=retry;q=expit(best.x[:2*C]).reshape(2,C);rates=decode(best.x)
    if q[1,int(spans[0]['record_c'])]<q[0,int(spans[0]['record_c'])]:q=q[::-1].copy();rates=rates[:,::-1].copy()
    out={'q_L':q[0].tolist(),'q_H':q[1].tolist(),'loglik':float(-best.fun),'success':bool(best.success),'gradient_max':float(np.max(np.abs(best.jac))),'attempts':attempts,'common_rates':common_rates,'positive_rho_constraint':positive_rho,'initial_state':'stationary independently at each span','spans':[]}
    for i,(n,R,const) in enumerate(prepared):
        u,d=rates[0 if common_rates else i];ll,g,xi,le=fb(n,R,q,u,d);v=derived(u,d);v.update({'id':spans[i].get('id',str(i)),'loglik':float(ll+const),'posterior_occupancy':float(g.mean()),'initial_posterior_H':float(g[0]),'expected_transition_counts':xi.tolist()})
        if return_series:
            path=np.empty(n.shape[1],dtype=np.uint8);LIB.hmm_viterbi(len(path),ptr(le),u,d,path.ctypes.data_as(U));v.update({'posterior_H':g.tolist(),'path':path.tolist(),'decoded_occupancy':float(path.mean())})
        out['spans'].append(v)
    return out
def simulate_span(span,fit,q_H,q_L,rng,with_rows=False):
    R=np.asarray(span['R'],dtype=int);N=np.asarray(span['n']).shape[1];path=np.empty(N,dtype=np.uint8);r=np.ascontiguousarray(rng.random(N),dtype=np.float64);u,d=fit['u'],fit['d'];LIB.hmm_path(N,ptr(r),u,d,path.ctypes.data_as(U));q=np.array([q_L,q_H],dtype=np.float64)
    s={k:v for k,v in span.items() if k not in ('n','rows','row_arrays')};s['n']=rng.binomial(R[:,None],q[path].T).astype(np.float64);s['latent_path']=path
    if with_rows:
        rows=[(rng.random((int(R[c]),N))<q[path,c]).astype(np.float64) for c in range(len(R))];s['row_arrays']=rows;s['n']=np.array([a.sum(axis=0) for a in rows],dtype=np.float64)
    return s
def fit_bootstrap(spans,fit,draws,seed,return_raw=True):
    rng=np.random.default_rng(seed);q=np.array([fit['q_L'],fit['q_H']]);samples=[];failures=[]
    for z in range(draws):
        sim=[simulate_span(s,f,fit['q_H'],fit['q_L'],rng) for s,f in zip(spans,fit['spans'])]
        f=fit_job(sim,q_init=q,rate_init=[[v['u'],v['d']] for v in fit['spans']],starts=1,return_series=False)
        if not f['success']:failures.append({'draw':z,'attempts':f['attempts']})
        samples.append({'q_H':f['q_H'],'q_L':f['q_L'],'spans':f['spans']})
    def interval(a):
        v=np.array([np.nan if x is None else x for x in a]);good=np.isfinite(v);return {'ci90':np.quantile(v[good],[.05,.95]).tolist() if good.any() else None,'finite':int(good.sum()),'total':len(v)}
    result={'draws':draws,'seed':seed,'failures':failures,'emissions':{k:[interval([s[k][c] for s in samples]) for c in range(len(fit['q_H']))] for k in ('q_H','q_L')},'spans':[]}
    for i,s in enumerate(spans):result['spans'].append({'id':s.get('id',str(i)),**{k:interval([v['spans'][i][k] for v in samples]) for k in ('u','d','b','rho','ell','mean_dwell_H','mean_dwell_L')}})
    if return_raw:result['samples']=samples
    return result

def fit_grouped(groups,rates_per_group=False,starts=3):
    """Separate job emissions, constant rates in each job or shared across jobs."""
    G=len(groups);Cs=[len(g[0]['R']) for g in groups];offsets=np.r_[0,np.cumsum([2*c for c in Cs])];E=int(offsets[-1]);prepared=[[prep(s) for s in g] for g in groups]
    inits=[init_params(g) for g in groups];q0=np.concatenate([logit(x[0]).ravel() for x in inits]);rr=np.array([x[1].mean(axis=0) for x in inits]);rr=rr if rates_per_group else rr.mean(axis=0)[None,:]
    def objective(x):
        grad=np.zeros_like(x);ll=0.;rates=expit(x[E:]).reshape(-1,2)
        for gi,gg in enumerate(prepared):
            q=expit(x[offsets[gi]:offsets[gi+1]]).reshape(2,Cs[gi]);gq=np.zeros_like(q);ri=gi if rates_per_group else 0;u,d=rates[ri];gu=gd=0.
            for n,R,const in gg:
                val,g,xi,_=fb(n,R,q,u,d);ll+=val+const;weights=np.array([1-g,g]);gq+=weights@n.T-weights.sum(axis=1)[:,None]*R[None,:]*q
                gu+=xi[1]/u-xi[0]/(1-u)+g[0]/u-1/(u+d);gd+=xi[2]/d-xi[3]/(1-d)+(1-g[0])/d-1/(u+d)
            grad[offsets[gi]:offsets[gi+1]]=gq.ravel();grad[E+2*ri]+=gu*u*(1-u);grad[E+2*ri+1]+=gd*d*(1-d)
        return -ll,-grad
    best=None;attempts=[]
    for factor in [1.,.4,2.][:starts]:
        x=np.r_[q0,logit(np.clip(rr*factor,1e-6,.999999)).ravel()];r=minimize(objective,x,jac=True,method='L-BFGS-B',bounds=[(-16,16)]*len(x),options={'ftol':1e-12,'gtol':1e-6,'maxiter':500,'maxls':30})
        attempts.append({'success':bool(r.success),'loglik':float(-r.fun),'gradient_max':float(np.max(abs(r.jac))),'iterations':int(r.nit),'message':str(r.message)})
        if best is None or r.fun<best.fun:best=r
    if not best.success:
        retry=minimize(objective,best.x,jac=True,method='L-BFGS-B',bounds=[(-16,16)]*len(best.x),options={'ftol':1e-10,'gtol':1e-5,'maxiter':1000,'maxls':100})
        attempts.append({'success':bool(retry.success),'loglik':float(-retry.fun),'gradient_max':float(np.max(abs(retry.jac))),'iterations':int(retry.nit),'message':str(retry.message),'retry':'Stationary start with numerical convergence tolerances relaxed after line search failure'})
        if retry.success and retry.fun<=best.fun+1e-7:best=retry
    rates=expit(best.x[E:]).reshape(-1,2);out={'loglik':float(-best.fun),'success':bool(best.success),'attempts':attempts,'groups':[],'rates_per_group':rates_per_group}
    for gi,gg in enumerate(prepared):
        q=expit(best.x[offsets[gi]:offsets[gi+1]]).reshape(2,Cs[gi]);u,d=rates[gi if rates_per_group else 0];f={'q_L':q[0].tolist(),'q_H':q[1].tolist(),'spans':[],'loglik':0.}
        for s,(n,R,const) in zip(groups[gi],gg):
            val,g,xi,le=fb(n,R,q,u,d);v=derived(u,d);v['id']=s['id'];v['loglik']=float(val+const);v['posterior_occupancy']=float(g.mean());f['spans'].append(v);f['loglik']+=v['loglik']
        out['groups'].append(f)
    return out
