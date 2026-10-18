"""Recount every archive input digest without modifying the input."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
checks=[]
for line in (ROOT/'input/SHA256SUMS').read_text().splitlines():
    if not line.strip(): continue
    expected,name=line.split(None,1); name=name.lstrip('*')
    actual=hashlib.sha256((ROOT/'input'/name).read_bytes()).hexdigest()
    checks.append({'file':name,'expected':expected,'actual':actual,'match':expected==actual})
actual_files={p.relative_to(ROOT/'input').as_posix() for p in (ROOT/'input').rglob('*') if p.is_file()}-{'SHA256SUMS'}
listed={x['file'] for x in checks}
result={'file_count':len(checks),'all_match':all(x['match'] for x in checks),
        'unlisted_files':sorted(actual_files-listed),'missing_files':sorted(listed-actual_files),'checks':checks}
(ROOT/'input-recheck.json').write_text(json.dumps(result,indent=2)+'\n')
assert result['all_match'] and not result['unlisted_files'] and not result['missing_files']
print('Input digests match:',len(checks))
