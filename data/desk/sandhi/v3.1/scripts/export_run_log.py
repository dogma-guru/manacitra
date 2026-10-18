"""Export current run tool inputs only, plus runtime and source seed metadata."""
from pathlib import Path
import json,gzip,sys,datetime
ROOT=Path(__file__).resolve().parents[1]
session=Path(sys.argv[1])
entries=[]
for line in session.read_text().splitlines():
    record=json.loads(line)
    if record.get('type')!='response_item':continue
    p=record.get('payload',{})
    if p.get('type') not in ('function_call','custom_tool_call'):continue
    entries.append({'timestamp':record.get('timestamp'),'type':p['type'],'name':p.get('name'),
        'input':p.get('arguments',p.get('input'))})
parts=['Model 01 version 3 run 3.1 operational record',
       'Only current run tool call inputs are exported. No outputs or earlier scientific results are imported.',
       'Scientific inputs are the supplied archive only. Runtime libraries are installed local dependencies.',
       'Final export UTC '+datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'RUNTIME\n'+(ROOT/'runtime.json').read_text(),
       'CURRENT RANDOM SEEDS: model check 310017 with 1000 draws per cell; joint forecast interval 310018 with 100000 draws. All ledgers deterministic.']
for p in sorted((ROOT/'input').rglob('fits*.json*')):
    raw=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
    meta=json.loads(raw).get('meta',{})
    parts.append('SOURCE FIT METADATA '+p.relative_to(ROOT).as_posix()+'\n'+json.dumps(meta,indent=2))
parts.append('ROOT EXACT CURRENT RUN TOOL INPUTS\n'+json.dumps(entries,indent=2))
for name in ['frequency-commands.log','shuffled-stamp-commands.log','monitor11-commands.log']:
    parts.append('AGENT EXACT CURRENT RUN TOOL INPUTS '+name+'\n'+(ROOT/name).read_text())
(ROOT/'run.log').write_text('\n\n'.join(parts)+'\n')
print('Root tool records exported:',len(entries))
