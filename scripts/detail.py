from common import CFG, ROOT, WORK, MODELS, ASSETS, N, WIDTH, HEIGHT
from pathlib import Path
import numpy as np,cv2,av
from fractions import Fraction
P=WORK/'full-test';cloud=np.load(CFG['points'])['points']
cap=cv2.VideoCapture(str(P/'Landmark-correction-silent.mp4'))
clean=np.load(P/'Clean-clay.npz')['frames']
outer=[61,185,40,39,37,0,267,269,270,409,291,375,321,405,314,17,84,181,91,146]
le=[33,246,161,160,159,158,157,173,133,155,154,153,145,144,163,7];re=[263,466,388,387,386,385,384,398,362,382,381,380,374,373,390,249]
lb=[70,63,105,66,107,55,65,52,53,46];rb=[336,296,334,293,300,276,283,282,295,285]
oval=[10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,378,400,377,152,148,176,149,150,136,172,58,132,93,234,127,162,21,54,103,67,109]
shots=np.load(WORK/'shots.npy')
stats={}
out=av.open(str(P/'Detail-assisted-test-silent.mp4'),'w');s=out.add_stream('libx264',rate=30);s.width=1536;s.height=568;s.pix_fmt='yuv420p';s.options={'crf':'16','preset':'fast'}
for i in range(N):
 ok,im=cap.read();assert ok
 if i==0 or shots[i]!=shots[i-1]:stats={}
 original=im[56:,:512];geom=im[56:,1024:].copy();xy=cloud[i,:,:2]*[1,-1];lo=xy[:468].min(0);hi=xy[:468].max(0);xy=(xy-(lo+hi)/2)*(440/max(hi-lo))+256;pt=np.round(xy).astype(np.int32)
 gray=cv2.cvtColor(original,cv2.COLOR_BGR2GRAY).astype(float)/255
 # Band-limited appearance residual. This is not recovered displacement or true surface geometry.
 illumination=cv2.GaussianBlur(gray,(0,0),12)
 local=(gray-illumination)/(illumination+.15)
 detail=np.clip(local*85,-50,50)
 facemask=np.zeros((512,512),np.uint8);cv2.fillPoly(facemask,[pt[oval]],255);facemask=cv2.GaussianBlur(facemask,(0,0),3)/255
 assist=np.clip(clean[i].astype(float)+detail[:,:,None]*facemask[:,:,None],0,255)
 # Restore original grayscale eye/lip interior cues, locally normalized, feathered at boundaries.
 for region,pad in [(le,3),(re,3),(outer,2),(lb,3),(rb,3)]:
  mask=np.zeros((512,512),np.uint8);cv2.fillPoly(mask,[pt[region]],255)
  mask=cv2.dilate(mask,np.ones((pad*2+1,pad*2+1),np.uint8));sel=gray[mask>0]
  low,high=np.percentile(sel,[3,97]);key=tuple(region)
  if key in stats: low,high=.85*np.array(stats[key])+.15*np.array([low,high])
  stats[key]=(low,high)
  patch=np.clip((gray-low)/max(high-low,.05),0,1)*185+12
  a=cv2.GaussianBlur(mask,(0,0),2.4)/255
  assist=assist*(1-a[:,:,None])+patch[:,:,None]*a[:,:,None]
 sourcexy=cloud[i,:,:2]*[1,-1];lo=sourcexy[:468].min(0);hi=sourcexy[:468].max(0);sc=440/max(hi-lo);center=(lo+hi)/2
 xx,yy=np.meshgrid(np.arange(512),np.arange(512));sx=(xx-256)/sc+center[0];sy=(yy-256)/sc+center[1];visible=(sx>=2)&(sx<WIDTH-2)&(sy>=2)&(sy<HEIGHT-2)
 visibility=cv2.GaussianBlur(visible.astype(np.float32),(0,0),1)[:,:,None];assist=assist*visibility+clean[i]*(1-visibility)
 assist=np.uint8(np.clip(assist,0,255));canvas=np.zeros((568,1536,3),np.uint8);canvas[56:]=np.concatenate([original,geom,assist],axis=1)
 for j,label in enumerate(['SOURCE','LANDMARK-CORRECTED','WITH SOURCE GRAYSCALE DETAIL']):cv2.putText(canvas,label,(512*j+12,35),cv2.FONT_HERSHEY_SIMPLEX,.55,(230,230,230),1,cv2.LINE_AA)
 vf=av.VideoFrame.from_ndarray(canvas,format='bgr24');vf.pts=i;vf.time_base=Fraction(1,30)
 for pk in s.encode(vf):out.mux(pk)
 if i in [30,60,90,120,150]:cv2.imwrite(str(P/f'detail-preview-{i}.jpg'),canvas)
for pk in s.encode():out.mux(pk)
out.close();print('DONE')
