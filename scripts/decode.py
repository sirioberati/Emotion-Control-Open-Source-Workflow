from common import CFG, ROOT, WORK, MODELS, ASSETS, N, WIDTH, HEIGHT
from pathlib import Path
import os,sys,inspect
import numpy as np
for n,t in {'float_':np.float64,'complex_':np.complex128,'unicode_':np.str_,'float':float,'int':int,'bool':bool,'object':object,'str':str,'complex':complex,'unicode':str}.items():
 if n not in np.__dict__:setattr(np,n,t)
inspect.getargspec=inspect.getfullargspec
import torch
P=WORK;os.chdir(MODELS/'smirk');sys.path.insert(0,str(MODELS/'smirk'))
from src.FLAME.FLAME import FLAME
torch.set_num_threads(4);flame=FLAME();d=np.load(P/'spectre-full-params.npz')
pars={k:torch.tensor(d[k]) for k in d.files if k.endswith('_params')};pars['shape_params']=torch.tensor(np.load(CFG['identity_reference']) if CFG.get('identity_reference') else np.median(d['shape_params'],axis=0))[None].repeat(len(d['frame']),1)
vv=[];lm=[]
with torch.inference_mode():
 for i in range(0,len(d['frame']),16):
  o=flame({k:v[i:i+16] for k,v in pars.items()});vv.append(o['vertices'].numpy());lm.append(o['landmarks_fan'].numpy())
np.savez_compressed(P/'spectre-full-geometry.npz',vertices=np.concatenate(vv),faces=np.load(ASSETS/'render-faces.npy'),landmarks=np.concatenate(lm),frame=d['frame'])
print('Decoded full clip, fixed original pilot identity shape')
