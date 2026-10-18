"""Delivery checks independent of the fitting helper."""
from pathlib import Path
import ast,json,hashlib,re
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(name,ok,detail=None):
    checks.append({'check':name,'pass':bool(ok),'detail':detail})
def load(n):return json.loads((ROOT/n).read_text())
for p in (ROOT/'scripts').glob('*.py'):
    ast.parse(p.read_text());check('Python syntax '+p.name,True)
expected=[(9,2,509,77,0),(9,3,349,55,0),(10,1,9100,125,1),(10,2,9033,124,0),(10,3,7073,98,0)]
F=load('frequency-ledger.json')
for t,j,nw,nf,ef in expected:
    w=F['summaries'][f't{t}j{j}:within_span'];f=F['summaries'][f't{t}j{j}:span_boundary']
    check(f'Required frequency comparison t{t}j{j}',(w['n_4khz'],w['events_4khz'],f['n_4khz'],f['events_4khz'])==(nw,0,nf,ef))
M=load('monitor11-ledger.json')
means=[round(r['mean_w'],3) for r in M['per_span']]
check('Six monitor means',means==[.340,.392,.360,.323,.350,.237],means)
check('Monitor within pair count',M['summary']['W_B']['trials']==285)
P=load('predictions-model-01-v3.json');R=load('rates-model-01-v3.json')
for name,digest in P['source_hashes'].items():check('Frozen prediction input '+name,hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest)
for design,count in [('shuffled',(16,38)),('monitor',(4,4))]:
    rate=R['classes']['B|own']['design'][design]
    check('B class '+design,(rate['events'],rate['trials'])==count)
    forecast=P['third_day']['weight_boundaries_'+design]
    check('B prediction class '+design,forecast['rate_path']=='classes.B|own.design.'+design and forecast['source_rate']['posterior']==rate['posterior'])
C=load('model-check-model-01-v3.json')
check('Model check has 1000 draws per eligible cell',all(len(c['fixed_counts'])==1000 and len(c['posterior_predictive_counts'])==1000 for c in C['cells'] if c.get('observed') is not None))
check('Test 11 frequency censor cells explicit',all(any(c['test']==11 and c['floor']=='4kHz' and c['channel']==ch and c.get('observed') is None for c in C['cells']) for ch in ['W','F']))
for name in ['report-model-01-v3.md','predictions-model-01-v3.md']:
    text=(ROOT/name).read_text();plain=re.sub(r'`[^`]*`','',text)
    forbidden=re.findall(r'\b(?:proves|reveals|kill|verified|benchmark|telegraph|parity|defect)\b',plain,re.I)
    check('Prose word restrictions '+name,not forbidden,forbidden)
    # Hyphens inside machine timestamps, scientific exponents and table syntax are data syntax.
    plain=re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z','',plain)
    plain=re.sub(r'e-\d+','',plain)
    plain='\n'.join(x for x in plain.splitlines() if not re.match(r'^\|[- |]+\|$',x))
    check('No prose dashes '+name,not re.search(r'[—–-]',plain))
for name in ['report-model-01-v3.md','events-model-01-v3.json','rates-model-01-v3.json','dependence-model-01-v3.json',
             'model-check-model-01-v3.json','estimators-model-01-v3.json','predictions-model-01-v3.md','predictions-model-01-v3.json']:
    check('Required deliverable '+name,(ROOT/name).is_file())
audit=load('frequency-stat-audit.json')
check('Independent frequency statistical audit',audit['all_numerical_checks_pass'] and not audit['scope_issues'])
audit=load('prediction-audit.json')
check('Independent prediction audit',audit['all_numeric_and_scope_checks_pass'] and not audit['findings'])
check('Prediction audit covers delivered JSON',audit['prediction_json_sha256']==hashlib.sha256((ROOT/'predictions-model-01-v3.json').read_bytes()).hexdigest())
check('Prediction audit covers delivered prose',audit['prediction_markdown_sha256']==hashlib.sha256((ROOT/'predictions-model-01-v3.md').read_bytes()).hexdigest())
result={'checks':checks,'all_pass':all(x['pass'] for x in checks),'count':len(checks),
    'scope':'Input identity, required counts, model selection, forecast source identity, syntax and prose. Independent scientific audits remain separate.'}
(ROOT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
assert result['all_pass'],[x for x in checks if not x['pass']]
print('Delivery checks passed:',len(checks))
