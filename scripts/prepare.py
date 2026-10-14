from common import executable
from common import CFG,ROOT,WORK,MODELS,ASSETS
from pathlib import Path
import os,json,subprocess,shutil,numpy as np,cv2,mediapipe as mp
ff=executable('ffmpeg');probe=executable('ffprobe')
path=WORK/'source.mp4';args=[ff,'-hide_banner','-loglevel','error','-y','-ss',str(CFG['start']),'-i',CFG['input']]
if CFG.get('duration') is not None:args+=['-t',str(CFG['duration'])]
args+=['-map','0:v:0','-map','0:a:0?','-vf',"scale='min(1920,iw)':-2,fps=30",'-c:v','libx264','-threads','4','-crf','16','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(path)]
subprocess.run(args,check=True)
info=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-of','json',str(path)]));v=next(s for s in info['streams'] if s['codec_type']=='video');N=int(v['nb_frames']);W=int(v['width']);H=int(v['height'])
CFG.update(video=str(path),frames=N,width=W,height=H,points=str(WORK/'points.npz'),has_audio=any(s['codec_type']=='audio' for s in info['streams']))
if CFG.get('reuse_tracking'):
 raw=np.load(CFG['reuse_tracking']);points=raw['points'];assert len(points)==N,'Reuse requires full matching clip and frame count';np.savez_compressed(WORK/'points.npz',**{k:raw[k] for k in raw.files})
else:
 clouds=[];rots=[];blends=[];shots=[];shot=0;prev=None
 opts=mp.tasks.vision.FaceLandmarkerOptions(base_options=mp.tasks.BaseOptions(model_asset_path=str(ASSETS/'face_landmarker.task')),running_mode=mp.tasks.vision.RunningMode.VIDEO,num_faces=1,min_face_detection_confidence=.35,min_face_presence_confidence=.35,min_tracking_confidence=.35,output_face_blendshapes=True,output_facial_transformation_matrixes=True)
 cap=cv2.VideoCapture(str(path));det=mp.tasks.vision.FaceLandmarker.create_from_options(opts)
 for i in range(N):
  ok,im=cap.read();assert ok
  small=cv2.resize(im,(64,36)).astype(np.float32)/255
  if prev is not None and np.mean(abs(small-prev))>.19:
   shot+=1;det.close();det=mp.tasks.vision.FaceLandmarker.create_from_options(opts)
  prev=small;shots.append(shot)
  result=det.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,data=np.ascontiguousarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB))),round(i*1000/30))
  if not result.face_landmarks:raise RuntimeError(f'No usable face at frame {i} ({i/30:.2f}s). Trim this section or review tracking; no face is fabricated.')
  points=np.array([[q.x*W,-q.y*H,-q.z*W] for q in result.face_landmarks[0]],np.float32);clouds.append(points)
  mat=np.array(result.facial_transformation_matrixes[0])[:3,:3];u,s,vt=np.linalg.svd(mat);rots.append(u@vt);blends.append({b.category_name:float(b.score) for b in result.face_blendshapes[0]})
 det.close();cap.release();points=np.array(clouds);np.savez_compressed(WORK/'points.npz',points=points,head_rotation=np.array(rots),time=np.arange(N)/30);np.save(WORK/'shots.npy',np.array(shots));(WORK/'Blendshapes.json').write_text(json.dumps(blends))
if CFG.get('map_project'):
 maps=Path(CFG['map_project'])/'work';f=np.load(maps/'fused.npz');assert len(f['land'])==N,'Map project does not match video frame count'
 assert CFG['start']==0 and CFG.get('duration') is None,'External maps require the complete original clip at matching resolution/FPS'
 for name in ['uvrelief','uvgloss']:
  assert all((maps/name/f'{i:04d}.png').exists() for i in range(N)),f'Missing {name} frames'
 np.save(WORK/'shots.npy',f['shot']);CFG['maps']=str(maps)
else:
 if not (WORK/'shots.npy').exists():np.save(WORK/'shots.npy',np.zeros(N,dtype=int))
 maps=WORK/'maps';maps.mkdir(exist_ok=True);CFG['maps']=str(maps)
 land=points*np.array([1,-1,-1]);np.savez_compressed(maps/'fused.npz',land=land,shot=np.load(WORK/'shots.npy'))
 for name in ['uvrelief','uvgloss']:(maps/name).mkdir(exist_ok=True)
 # Same luminance-bandpass and specular-peak construction used in the supplied project.
 obj=(ASSETS/'canonical_face_model.obj').read_text().splitlines();vt=np.array([[float(x) for x in l.split()[1:3]] for l in obj if l.startswith('vt ')]);tri=[]
 for l in obj:
  if l.startswith('f '):
   parts=[p.split('/') for p in l.split()[1:4]];tri.append(([int(p[0])-1 for p in parts],[int(p[1])-1 for p in parts]))
 uvpx=np.stack([vt[:,0]*1024,(1-vt[:,1])*1024],1).astype(np.float32)
 def warp(img,pts,fill):
  out=np.full((1024,1024),fill,np.float32);acc=np.zeros((1024,1024),np.uint8)
  for vi,ti in tri:
   src=pts[vi].astype(np.float32);dst=uvpx[ti]
   if src[:,0].min()<2 or src[:,1].min()<2 or src[:,0].max()>W-3 or src[:,1].max()>H-3:continue
   x0,y0=np.maximum(np.floor(dst.min(0)).astype(int),0);x1,y1=np.minimum(np.ceil(dst.max(0)).astype(int)+1,1024)
   if x1<=x0 or y1<=y0:continue
   m=cv2.getAffineTransform(src,(dst-[x0,y0]).astype(np.float32));patch=cv2.warpAffine(img,m,(x1-x0,y1-y0),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE);mask=np.zeros((y1-y0,x1-x0),np.uint8);cv2.fillConvexPoly(mask,np.round(dst-[x0,y0]).astype(np.int32),1)
   region=out[y0:y1,x0:x1];region[mask>0]=patch[mask>0];acc[y0:y1,x0:x1]|=mask
  return out,acc
 eyes=[[33,7,163,144,145,153,154,155,133,173,157,158,159,160,161,246],[362,382,381,380,374,373,390,249,263,466,388,387,386,385,384,398]];lips=[61,146,91,181,84,17,314,405,321,375,291,409,270,269,267,0,37,39,40,185]
 cap=cv2.VideoCapture(str(path))
 for i in range(N):
  ok,img=cap.read();assert ok;L=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY).astype(np.float32)/255;pts=land[i,:,:2];skin=np.zeros((H,W),np.uint8);cv2.fillConvexPoly(skin,cv2.convexHull(pts[:468].astype(np.int32)),1);skin=cv2.erode(skin,np.ones((9,9),np.uint8));holes=np.zeros((H,W),np.uint8)
  for ids in eyes+[lips]:cv2.fillPoly(holes,[pts[ids].astype(np.int32)],1)
  holes=cv2.dilate(holes,np.ones((7,7),np.uint8));size=max(np.ptp(pts[:468,0]),np.ptp(pts[:468,1]));s1,s2=max(size/400,.8),max(size/60,3)
  band=cv2.GaussianBlur(L,(0,0),s1)-cv2.GaussianBlur(L,(0,0),s2);local=cv2.GaussianBlur(abs(band),(0,0),s2*3)+.03;rel=np.clip(band/local*.5,-1,1)*skin
  spec=L-cv2.GaussianBlur(L,(0,0),s2);peak=((spec>.09)&(L>.35)).astype(np.uint8)*skin*(1-holes);gloss=cv2.GaussianBlur(peak.astype(np.float32),(0,0),1.2);eye=np.zeros((H,W),np.uint8)
  for ids in eyes:cv2.fillPoly(eye,[pts[ids].astype(np.int32)],1)
  gloss=np.clip(gloss*2.5+eye*.9,0,1);r,acc=warp((rel*.5+.5)*255,pts,127.5);g,_=warp(gloss*255,pts,0);r=cv2.GaussianBlur(r,(0,0),.8);r[acc==0]=127.5
  cv2.imwrite(str(maps/'uvrelief'/f'{i:04d}.png'),np.clip(r,0,255).astype(np.uint8));cv2.imwrite(str(maps/'uvgloss'/f'{i:04d}.png'),np.clip(g,0,255).astype(np.uint8))
  if i%100==0:print('UV maps',i,flush=True)
 cap.release()
Path(os.environ['CAPTURE_CONFIG']).write_text(json.dumps(CFG,indent=2));print('Prepared',N,'frames',W,H)
