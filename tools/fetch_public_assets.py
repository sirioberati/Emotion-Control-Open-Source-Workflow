"""Fetch pinned upstream code and MediaPipe files; never download FLAME weights."""
from pathlib import Path
import hashlib,json,subprocess,urllib.request
ROOT=Path(__file__).resolve().parents[1]
REPOS={
 'spectre':('https://github.com/filby89/spectre.git','0b339a8486ab0869466d145628be03c56eb6c2b9'),
 'smirk':('https://github.com/georgeretsi/smirk.git','c7de404c4389f073906a6db1adabf62efcea3f35'),
}
for name,(url,commit) in REPOS.items():
 path=ROOT/'models'/name
 if not path.exists():
  path.parent.mkdir(exist_ok=True);subprocess.run(['git','clone','--no-checkout',url,str(path)],check=True)
  subprocess.run(['git','-C',str(path),'checkout','--detach',commit],check=True)
 else:
  actual=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
  if actual!=commit:raise SystemExit(f'{path}: expected {commit}; existing checkout left unchanged.')
assets=ROOT/'assets';assets.mkdir(exist_ok=True)
manifest=json.loads((ROOT/'config/public-assets.json').read_text())
for name,entry in manifest.items():
 path=assets/name
 if not path.exists():
  with urllib.request.urlopen(entry['url'],timeout=90) as response:data=response.read()
  if hashlib.sha256(data).hexdigest()!=entry['sha256']:raise SystemExit('Checksum mismatch: '+name)
  path.write_bytes(data)
 elif hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:raise SystemExit('Existing file checksum mismatch: '+name)
print('Public assets ready. Obtain FLAME and the SPECTRE checkpoint as described in docs/SETUP.md.')
