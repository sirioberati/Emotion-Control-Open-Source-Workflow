"""Build the exact approved topology locally from separately licensed assets."""
from pathlib import Path
import hashlib,inspect,json,os,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
for name,value in {'float_':np.float64,'complex_':np.complex128,'unicode_':np.str_,'float':float,'int':int,'bool':bool,'object':object,'str':str,'complex':complex,'unicode':str}.items():
 if name not in np.__dict__:setattr(np,name,value)
inspect.getargspec=inspect.getfullargspec
repo=ROOT/'models/smirk';os.chdir(repo);sys.path.insert(0,str(repo))
from src.FLAME.FLAME import FLAME
recipe=json.loads((ROOT/'config/asset-selection.json').read_text());assets=ROOT/'assets';assets.mkdir(exist_ok=True)
faces=FLAME().faces_tensor.numpy()
if hashlib.sha256(faces.astype('<i8').tobytes()).hexdigest()!=recipe['flame_faces_sha256']:
 raise SystemExit('FLAME topology differs from the approved FLAME 2020 model. Do not substitute a different version.')
selected=faces[recipe['flame_face_indices']]
assert hashlib.sha256(selected.astype('<i8').tobytes()).hexdigest()==recipe['render_faces_sha256']
obj=assets/'canonical_face_model.obj'
if hashlib.sha256(obj.read_bytes()).hexdigest()!=recipe['canonical_sha256']:
 raise SystemExit('Canonical MediaPipe mesh differs from the approved asset. See docs/SETUP.md.')
triangles=[]
for line in obj.read_text().splitlines():
 if line.startswith('f '):triangles.append([int(x.split('/')[0])-1 for x in line.split()[1:4]])
np.save(assets/'render-faces.npy',selected)
np.save(assets/'outline-vertices.npy',np.array(recipe['outline_vertex_indices'],dtype=np.int64))
# The renderer only consumes the set of triangles, never the pilot iris coordinates.
np.savez_compressed(assets/'mesh_topology.npz',faces=np.array(triangles,dtype=np.int64)[recipe['canonical_triangle_indices']])
print('Approved topology prepared. Licensed geometry stays in the ignored assets directory.')
