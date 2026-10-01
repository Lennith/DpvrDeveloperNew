#!/usr/bin/env python3
"""Package source + built pages, excluding evidence captures, binaries and caches."""
import hashlib,json,sys,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];out=Path(sys.argv[1]);out.parent.mkdir(parents=True,exist_ok=True)
files=[p for d in ['assets','content','docs','public','tools'] for p in (R/d).rglob('*') if p.is_file() and '__pycache__' not in p.parts]+[R/'README.md',R/'requirements.txt',R/'.gitignore']
manifest={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(files):z.write(p,'DpvrDeveloperNew/'+str(p.relative_to(R)))
 z.writestr('SHA256SUMS.json',json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'file':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'files':len(files)}))
