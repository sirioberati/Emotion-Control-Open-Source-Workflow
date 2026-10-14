from common import CFG, ROOT, WORK, MODELS, ASSETS, N, WIDTH, HEIGHT
from pathlib import Path
import os,sys,inspect,pickle,json
import numpy as np
for n,t in {'float_':np.float64,'complex_':np.complex128,'unicode_':np.str_,'float':float,'int':int,'bool':bool,'object':object,'str':str,'complex':complex,'unicode':str}.items():
 if n not in np.__dict__:setattr(np,n,t)
inspect.getargspec=inspect.getfullargspec
import cv2,av,torch
from numba import njit
from scipy import sparse
from scipy.sparse.linalg import splu
from scipy.ndimage import gaussian_filter1d
from fractions import Fraction
P=WORK;O=P/'full-test';O.mkdir(exist_ok=True)
os.chdir(MODELS/'smirk');sys.path.insert(0,str(MODELS/'smirk'))
from src.FLAME.FLAME import FLAME
torch.set_num_threads(4);flame=FLAME();fullfaces=flame.faces_tensor.numpy()
from raster import raster
d=np.load(P/'spectre-full-params.npz');geo=np.load(P/'spectre-full-geometry.npz');V=geo['vertices'].copy();F=geo['faces']
shots=np.load(WORK/'shots.npy')
starts=np.r_[0,np.flatnonzero(np.diff(shots))+1];ends=np.r_[starts[1:],len(shots)]
for a,z in zip(starts,ends):V[a:z]=gaussian_filter1d(V[a:z],.6,axis=0)
e=np.load('assets/mediapipe_landmark_embedding/mediapipe_landmark_embedding.npz');ids=e['landmark_indices'];ft=fullfaces[e['lmk_face_idx']];bary=e['lmk_b_coords']
points=np.load(CFG['points'])['points']
outer=[61,185,40,39,37,0,267,269,270,409,291,375,321,405,314,17,84,181,91,146,61]
inner=[78,191,80,81,82,13,312,311,310,415,308,324,318,402,317,14,87,178,88,95,78]
le=[33,246,161,160,159,158,157,173,133,155,154,153,145,144,163,7,33]
re=[263,466,388,387,386,385,384,398,362,382,381,380,374,373,390,249,263]
# Brow boundaries, directly tracked. Rendering is flat grayscale, not photo texture.
lb=[70,63,105,66,107,55,65,52,53,46];rb=[336,296,334,293,300,276,283,282,295,285]
cap=cv2.VideoCapture(CFG['video']);cap.set(cv2.CAP_PROP_POS_FRAMES,0)

out=av.open(str(O/'Landmark-correction-silent.mp4'),'w');s=out.add_stream('libx264',rate=30);s.width=1536;s.height=568;s.pix_fmt='yuv420p';s.options={'crf':'16','preset':'fast'}
errors=[];saved=[];clean=[];boundary_errors=[]
boundary=np.load(ASSETS/'outline-vertices.npy')
oval=[10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,378,400,377,152,148,176,149,150,136,172,58,132,93,234,127,162,21,54,103,67,109]
boundary_map=None
# Constrain barycentric positions directly. Surface-neighbor regularization avoids
# coupling the upper/lower lip merely because they are close in screen space.
nvtx=len(V[0]);edges=np.concatenate([fullfaces[:,[0,1]],fullfaces[:,[1,2]],fullfaces[:,[2,0]]]);edges=np.unique(np.sort(edges,axis=1),axis=0)
a=sparse.coo_matrix((np.ones(len(edges)*2),(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(nvtx,nvtx)).tocsr()
L=sparse.diags(np.array(a.sum(1)).ravel())-a
C=sparse.coo_matrix((np.r_[bary.ravel(),np.ones(len(boundary))],(np.r_[np.repeat(np.arange(len(ids)),3),len(ids)+np.arange(len(boundary))],np.r_[ft.ravel(),boundary])),shape=(len(ids)+len(boundary),nvtx)).tocsc()
H=(L.T@L + sparse.eye(nvtx)*.025).tocsc()
K=sparse.bmat([[H,C.T],[C,None]],format='csc');solver=splu(K)

for ii in range(N):
 i=ii;frame=ii;ok,im=cap.read();assert ok
 if i in starts:boundary_map=None
 q=points[frame];xy=q[:,:2]*[1,-1];lo=xy[:468].min(0);hi=xy[:468].max(0);center=(lo+hi)/2;scale=440/max(hi-lo)
 mat=np.array([[scale,0,256-center[0]*scale],[0,scale,256-center[1]*scale]])
 orig=cv2.warpAffine(im,mat,(512,512));targets=(xy-center)*scale+256
 v=V[i].copy();cam=d['cam'][i];tf=d['transforms'][i]
 proj=(v[:,:2]+cam[1:])*cam[0];proj[:,1]*=-1;proj=(proj+1)*112
 src=np.column_stack([proj,np.ones(len(proj))])@np.linalg.inv(tf).T
 pp=(src[:,:2]-center)*scale+256
 if boundary_map is None:
  # Establish a fixed angular correspondence for the outer boundary; no frame-to-frame rematching.
  def angles(p):
   mid=(p.min(0)+p.max(0))/2;v=(p-mid)/np.maximum(np.ptp(p,axis=0),1)
   return np.arctan2(v[:,1],v[:,0])
  ba=angles(pp[boundary]);ta=angles(targets[oval]);order=np.argsort(ta);a=ta[order]
  ext=np.r_[a[-1]-2*np.pi,a,a[0]+2*np.pi];ind=np.r_[order[-1],order,order[0]]
  hiidx=np.searchsorted(ext,ba).clip(1,len(ext)-1);lowidx=hiidx-1
  fraction=(ba-ext[lowidx])/(ext[hiidx]-ext[lowidx]);boundary_map=(ind[lowidx],ind[hiidx],fraction)
 left,right,frac=boundary_map;bt=targets[np.array(oval)[left]]*(1-frac[:,None])+targets[np.array(oval)[right]]*frac[:,None]
 baseline=pp.copy()
 target_constraint=np.concatenate([targets[ids],bt])
 residual=target_constraint-C@baseline
 rhs=np.vstack([np.zeros((nvtx,2)),residual])
 correction=solver.solve(rhs)[:nvtx]
 pp=baseline+correction
 anchors=(pp[ft]*bary[:,:,None]).sum(1);err=np.linalg.norm(anchors-targets[ids],axis=1);errors.append(err);boundary_errors.append(np.linalg.norm(pp[boundary]-bt,axis=1))
 # Reconstruct camera-space XY after the measured screen-space correction; retain estimated Z.
 srcnew=(pp-256)/scale+center
 cp=np.column_stack([srcnew,np.ones(len(srcnew))])@tf.T
 un=(cp[:,:2]/112-1);un[:,1]*=-1
 v[:,:2]=un/cam[0]-cam[1:]
 tri=v[F];nf=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);nv=np.zeros_like(v)
 for k in range(3):np.add.at(nv,F[:,k],nf)
 nv/=np.maximum(np.linalg.norm(nv,axis=1,keepdims=True),1e-8)
 corrected=raster(v,pp,F,nv)
 clean.append(corrected.copy())
 pts=np.round(targets).astype(np.int32)
 cv2.fillPoly(corrected,[pts[inner]],(7,7,7),cv2.LINE_AA)
 cv2.polylines(corrected,[pts[outer]],False,(100,100,100),1,cv2.LINE_AA)
 for eye,iris in [(le,[469,470,471,472]),(re,[474,475,476,477])]:
  eyemask=np.zeros((512,512),np.uint8);cv2.fillPoly(eyemask,[pts[eye]],255,cv2.LINE_AA)
  layer=np.full((512,512,3),185,np.uint8)
  ip=targets[iris];cent=ip.mean(0);a=(ip[0]-ip[2])/2;b=(ip[1]-ip[3])/2
  theta=np.linspace(0,2*np.pi,64);ring=cent+np.cos(theta)[:,None]*a+np.sin(theta)[:,None]*b
  cv2.fillPoly(layer,[np.round(ring).astype(np.int32)],(65,65,65),cv2.LINE_AA)
  pupil=cent+(ring-cent)*.4;cv2.fillPoly(layer,[np.round(pupil).astype(np.int32)],(15,15,15),cv2.LINE_AA)
  corrected[eyemask>0]=layer[eyemask>0]
  cv2.polylines(corrected,[pts[eye]],False,(70,70,70),1,cv2.LINE_AA)
 for brow in [lb,rb]:cv2.fillPoly(corrected,[pts[brow]],(65,65,65),cv2.LINE_AA)
 oldpanel=orig.copy()
 canvas=np.zeros((568,1536,3),np.uint8);canvas[56:]=np.concatenate([orig,oldpanel,corrected],axis=1)
 for j,label in enumerate(['SOURCE','SOURCE REPEAT','LANDMARK-CORRECTED + GAZE']):cv2.putText(canvas,label,(j*512+14,35),cv2.FONT_HERSHEY_SIMPLEX,.57,(230,230,230),1,cv2.LINE_AA)
 vf=av.VideoFrame.from_ndarray(canvas,format='bgr24');vf.pts=ii;vf.time_base=Fraction(1,30)
 for pk in s.encode(vf):out.mux(pk)
 if ii in [0,30,90,130,179]:cv2.imwrite(str(O/f'preview-{frame}.jpg'),canvas)
 saved.append(v)
 if ii%30==0:print('Corrected',ii,flush=True)
for pk in s.encode():out.mux(pk)
out.close();np.savez_compressed(O/'Clean-clay.npz',frames=np.array(clean));errors=np.array(errors)
np.save(O/'constraint-errors.npy',np.array(errors));np.savez_compressed(O/'Corrected-geometry.npz',vertices=np.array(saved),faces=F,frame=np.arange(N))
report={'frames':N,'fps':30,'embedded_constraints':105,'outline_constraints':56,'mean_outline_error_px':float(np.mean(boundary_errors)),'mean_constraint_error_px_at_512_crop':float(errors.mean()),'p95_error_px':float(np.percentile(errors,95)),'max_error_px':float(errors.max()),'method':'Topology-aware constrained surface fit; lightly stabilized 3D prior, per-frame lip and eye constraints retained','warning':'Error is against MediaPipe estimates, not ground truth. Iris position measured; pupil appearance synthetic. Z remains SPECTRE/FLAME estimate.'}
(O/'diagnostics.json').write_text(json.dumps(report,indent=2));print(report)
