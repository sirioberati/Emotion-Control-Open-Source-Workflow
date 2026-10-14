from common import CFG, ROOT, WORK, MODELS, ASSETS, N, WIDTH, HEIGHT
from pathlib import Path
import os,sys,inspect,json,pickle
import numpy as np
for n,t in {'float_':np.float64,'complex_':np.complex128,'unicode_':np.str_,'float':float,'int':int,'bool':bool,'object':object,'str':str,'complex':complex,'unicode':str}.items():
 if n not in np.__dict__:setattr(np,n,t)
inspect.getargspec=inspect.getfullargspec
import torch,cv2
from skimage.transform import estimate_transform,warp
from types import SimpleNamespace
P=WORK;kind='spectre';repo=MODELS/kind
os.chdir(repo);sys.path.insert(0,str(repo));torch.set_num_threads(4)
start,end=0,N
points=np.load(CFG['points'])['points']
cap=cv2.VideoCapture(CFG['video']);cap.set(cv2.CAP_PROP_POS_FRAMES,start)
ims=[];trans=[]
for i in range(start,end):
 ok,im=cap.read();assert ok
 xy=points[i,:468,:2]*[1,-1];lo=xy.min(0);hi=xy.max(0)
 if kind=='spectre':lo[1]=xy[[70,63,105,66,107,336,296,334,293,300],1].min()
 center=(lo+hi)/2;size=int((hi-lo).mean()*(1.4 if kind=='smirk' else 1.6))
 src=np.array([center+[-size/2,-size/2],center+[-size/2,size/2],center+[size/2,-size/2]])
 tf=estimate_transform('similarity',src,np.array([[0,0],[0,223],[223,0]]))
 crop=warp(cv2.cvtColor(im,cv2.COLOR_BGR2RGB),tf.inverse,output_shape=(224,224))
 ims.append(crop.transpose(2,0,1));trans.append(tf.params)
cap.release();X=torch.tensor(np.array(ims),dtype=torch.float32)
if kind=='smirk':
 from src.smirk_encoder import SmirkEncoder
 model=SmirkEncoder().eval();checkpoint=torch.load(repo/'pretrained_models/SMIRK_em1.pt',map_location='cpu',weights_only=True)
 model.load_state_dict({k.replace('smirk_encoder.',''):v for k,v in checkpoint.items() if 'smirk_encoder' in k})
 parts=[]
 with torch.inference_mode():
  for i in range(0,len(X),8):
   parts.append(model(X[i:i+8]));print(kind,i,flush=True)
 params={k:torch.cat([d[k] for d in parts]) for k in parts[0]}
else:
 import torchvision
 torch.hub.load=lambda *a,**kw:torchvision.models.mobilenet_v2(weights=None)
 from src.models import resnet
 resnet.load_ResNet50Model=lambda:resnet.ResNet(resnet.Bottleneck,[3,4,6,3])
 from src.models.encoders import ResnetEncoder,PerceptualEncoder
 base=ResnetEncoder(236).eval();expr=PerceptualEncoder(50,SimpleNamespace(backbone='mobilenetv2')).eval()
 c=torch.load(repo/'pretrained/spectre_model.tar',map_location='cpu',weights_only=True);c=c.get('state_dict',c)
 if 'E_flame' in c:st=c
 else:
  st={a:{k.replace('deca.','').replace(a+'.',''):v for k,v in c.items() if a+'.' in k} for a in ['E_flame','E_expression']}
 print(base.load_state_dict(st['E_flame']),expr.load_state_dict(st['E_expression']),flush=True)
 bs=[];features=[]
 with torch.inference_mode():
  for i in range(0,len(X),8):
   xx=X[i:i+8];bs.append(base(xx));features.append(torch.nn.functional.adaptive_avg_pool2d(expr.encoder.features(xx),(1,1)).flatten(1));print(kind,i,flush=True)
  b=torch.cat(bs);f=torch.cat(features);e=torch.empty((len(f),53))
  shots=np.load(WORK/'shots.npy');starts=np.r_[0,np.flatnonzero(np.diff(shots))+1];ends=np.r_[starts[1:],len(shots)]
  for a,z in zip(starts,ends):
   local=f[a:z];pad=torch.cat([local[:1].repeat(2,1),local,local[-1:].repeat(2,1)],0)
   e[a:z]=expr.layers(expr.temporal(pad.T[None]).squeeze(0).T)[2:-2]
  e[:,50]=torch.relu(e[:,50])
 params={'shape_params':torch.nn.functional.pad(b[:,:100],(0,200)),'expression_params':b[:,150:200]+e[:,:50],'pose_params':b[:,200:203],'jaw_params':b[:,203:206]+e[:,50:],'cam':b[:,206:209]}
np.savez(P/(kind+'-full-params.npz'),**{k:v.numpy() for k,v in params.items()},transforms=np.array(trans),frame=np.arange(start,end))
print('DONE',kind,flush=True)
