"""Create the file manifest and ZIP, then recount every archived digest."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
for path in (ROOT/'scripts').glob('__pycache__/*'):
    if path.is_file():path.unlink()
cache=ROOT/'scripts/__pycache__'
if cache.exists() and not any(cache.iterdir()):cache.rmdir()
paths=sorted(p for p in ROOT.rglob('*') if p.is_file() and p!=ROOT/'SHA256SUMS')
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in paths)
(ROOT/'SHA256SUMS').write_text(manifest)
archive=ROOT.parent/'model-01-v3.1.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(ROOT.rglob('*')):
        if p.is_file():z.write(p,ROOT.name+'/'+p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    entries=z.read(ROOT.name+'/SHA256SUMS').decode().splitlines()
    for line in entries:
        expected,name=line.split(None,1)
        assert hashlib.sha256(z.read(ROOT.name+'/'+name)).hexdigest()==expected,name
    assert len(z.namelist())==len(entries)+1
digest=hashlib.sha256(archive.read_bytes()).hexdigest()
Path(str(archive)+'.sha256').write_text(digest+'  '+archive.name+'\n')
print(json.dumps({'archive':str(archive),'sha256':digest,'manifest_files':len(entries),
                  'archive_members':len(entries)+1,'bytes':archive.stat().st_size,'all_archived_hashes_match':True},indent=2))
