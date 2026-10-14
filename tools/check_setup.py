"""Report required runtime, binaries and model assets without starting a render."""
from pathlib import Path
import importlib.util,os,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
missing=[]
for module in ['numpy','scipy','torch','torchvision','mediapipe','cv2','numba','av','skimage','chumpy']:
 if importlib.util.find_spec(module) is None:missing.append('Python package: '+module)
for binary in ['ffmpeg','ffprobe']:
 if not shutil.which(os.environ.get(binary.upper(),binary)):missing.append('Executable: '+binary)
for path in [
 'models/spectre/src/models/encoders.py','models/spectre/pretrained/spectre_model.tar',
 'models/smirk/src/FLAME/FLAME.py','models/smirk/assets/FLAME2020/generic_model.pkl',
 'models/smirk/assets/landmark_embedding.npy','models/smirk/assets/l_eyelid.npy','models/smirk/assets/r_eyelid.npy',
 'models/smirk/assets/mediapipe_landmark_embedding/mediapipe_landmark_embedding.npz',
 'assets/face_landmarker.task','assets/canonical_face_model.obj','assets/render-faces.npy','assets/outline-vertices.npy','assets/mesh_topology.npz',
]:
 if not (ROOT/path).is_file():missing.append('File: '+path)
if missing:
 print('Setup incomplete:\n'+'\n'.join('  - '+item for item in missing))
 print('Follow docs/SETUP.md, then run this check again.');sys.exit(1)
print('Required packages, executables and assets found. Run a short pilot to validate inference.')
