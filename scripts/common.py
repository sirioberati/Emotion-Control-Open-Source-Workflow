import json, os
from pathlib import Path
CFG=json.loads(Path(os.environ['CAPTURE_CONFIG']).read_text())
ROOT=Path(__file__).resolve().parent.parent
WORK=Path(CFG['work']);MODELS=ROOT/'models';ASSETS=ROOT/'assets'
N=CFG.get('frames',0);WIDTH=CFG.get('width',0);HEIGHT=CFG.get('height',0)

# Portable executable discovery; no changes to rendering or fitting math.
def executable(name):
 import shutil
 value=os.environ.get(name.upper()) or shutil.which(name)
 if not value:raise RuntimeError(f"Missing {name}. Install FFmpeg and ensure it is on PATH.")
 return value
