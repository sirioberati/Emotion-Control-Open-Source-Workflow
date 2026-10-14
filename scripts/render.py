from common import executable
from common import CFG, ROOT, WORK, MODELS, ASSETS, N, WIDTH, HEIGHT
from pathlib import Path
from fractions import Fraction
import numpy as np,cv2,av,subprocess,json,shutil
from numba import njit
P=WORK;R=Path(CFG['maps']);root=P/'full-test';O=Path(CFG['output']);O.mkdir(parents=True,exist_ok=True)
points=np.load(CFG['points'])['points'];geo=np.load(P/'full-test/Corrected-geometry.npz');d=np.load(P/'spectre-full-params.npz');clean=np.load(P/'full-test/Clean-clay.npz')['frames'];ff=geo['faces'];fused=np.load(R/'fused.npz')['land'];top=np.load(ASSETS/'mesh_topology.npz');validfaces={tuple(sorted(x)) for x in top['faces']}
lines=(ASSETS/'canonical_face_model.obj').read_text().splitlines();uv=np.array([[float(x) for x in l.split()[1:3]] for l in lines if l.startswith('vt ')],np.float32);faces=[];tuv=[];allfaces=[];alluv=[]
for l in lines:
 if l.startswith('f '):
  pair=[x.split('/') for x in l.split()[1:4]];vi=[int(x[0])-1 for x in pair];ti=[int(x[1])-1 for x in pair]
  allfaces.append(vi);alluv.append(uv[ti])
  if tuple(sorted(vi)) in validfaces: faces.append(vi);tuv.append(uv[ti])
allfaces=np.array(allfaces);alluv=np.array(alluv);alluv[:,:,0]*=1024;alluv[:,:,1]=(1-alluv[:,:,1])*1024
faces=np.array(faces);tuv=np.array(tuv);tuv[:,:,0]*=1024;tuv[:,:,1]=(1-tuv[:,:,1])*1024
@njit
def uvmap(xy,source,faces,tuv):
 maps=np.full((512,512,2),-1.,np.float32)
 for fi in range(len(faces)):
  ids=faces[fi];a,b,c=xy[ids[0]],xy[ids[1]],xy[ids[2]]
  valid=True
  for ix in ids:
   if source[ix,0]<2 or source[ix,0]>WIDTH-3 or source[ix,1]<2 or source[ix,1]>HEIGHT-3:valid=False
  if not valid:continue
  den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<.1:continue
  x0=max(0,int(np.floor(min(a[0],b[0],c[0]))));x1=min(511,int(np.ceil(max(a[0],b[0],c[0]))));y0=max(0,int(np.floor(min(a[1],b[1],c[1]))));y1=min(511,int(np.ceil(max(a[1],b[1],c[1]))))
  for y in range(y0,y1+1):
   for x in range(x0,x1+1):
    wa=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den;wb=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;wc=1-wa-wb
    if min(wa,wb,wc)<-.001:continue
    maps[y,x]=wa*tuv[fi,0]+wb*tuv[fi,1]+wc*tuv[fi,2]
 return maps
@njit
def normbuffer(v,xy,faces,norms):
 buf=np.zeros((512,512,3),np.float32);zbuf=np.full((512,512),-1e10)
 for ids in faces:
  a,b,c=xy[ids[0]],xy[ids[1]],xy[ids[2]];den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-8:continue
  x0=max(0,int(np.floor(min(a[0],b[0],c[0]))));x1=min(511,int(np.ceil(max(a[0],b[0],c[0]))));y0=max(0,int(np.floor(min(a[1],b[1],c[1]))));y1=min(511,int(np.ceil(max(a[1],b[1],c[1]))))
  for y in range(y0,y1+1):
   for x in range(x0,x1+1):
    wa=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den;wb=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;wc=1-wa-wb
    if min(wa,wb,wc)<-.001:continue
    z=wa*v[ids[0],2]+wb*v[ids[1],2]+wc*v[ids[2],2]
    if z<zbuf[y,x]:continue
    n=wa*norms[ids[0]]+wb*norms[ids[1]]+wc*norms[ids[2]];n=n/max(np.sqrt((n*n).sum()),1e-9);buf[y,x]=n;zbuf[y,x]=z
 return buf
outer=[61,185,40,39,37,0,267,269,270,409,291,375,321,405,314,17,84,181,91,146]
le=[33,246,161,160,159,158,157,173,133,155,154,153,145,144,163,7];re=[263,466,388,387,386,385,384,398,362,382,381,380,374,373,390,249];lb=[70,63,105,66,107,55,65,52,53,46];rb=[336,296,334,293,300,276,283,282,295,285]
cap=cv2.VideoCapture(str(root/'Original-and-detailed-mesh.mp4'));previous=cv2.VideoCapture(str(root/'Original-and-detailed-mesh.mp4'));writers=[]
for name in ['sculpted-source-silent','sculpted-before-after-silent']:
 o=av.open(str(P/(name+'.mp4')),'w');s=o.add_stream('libx264',rate=30);s.width=1024;s.height=568;s.pix_fmt='yuv420p';s.options={'crf':'15','preset':'fast'};writers.append((o,s))
stats=[]
for i in range(N):
 ok,frame=cap.read();assert ok
 xy=points[i,:,:2]*[1,-1];lo=xy[:468].min(0);hi=xy[:468].max(0);center=(lo+hi)/2;scale=440/max(hi-lo);target=(xy-center)*scale+256;pts=np.round(target).astype(np.int32)
 maps=uvmap(target,fused[i,:,:2],faces,tuv)
 glossmap=uvmap(target,fused[i,:,:2],allfaces,alluv)
 rel=cv2.imread(str(R/'uvrelief'/f'{i:04d}.png'),0);gl=cv2.imread(str(R/'uvgloss'/f'{i:04d}.png'),0);assert rel is not None and gl is not None
 height=cv2.remap((rel.astype(np.float32)-127.5)/127.5,maps[:,:,0],maps[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
 gloss=cv2.remap(gl.astype(np.float32)/255,glossmap[:,:,0],glossmap[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
 valid=(maps[:,:,0]>=0).astype(np.float32);valid=cv2.erode(valid,np.ones((5,5),np.uint8));valid=cv2.GaussianBlur(valid,(0,0),1.5)
 height=cv2.GaussianBlur(height,(0,0),1.0);gloss=cv2.GaussianBlur(gloss,(0,0),1.0)*(glossmap[:,:,0]>=0)
 dx=cv2.Sobel(height,cv2.CV_32F,1,0,ksize=3)/8;dy=cv2.Sobel(height,cv2.CV_32F,0,1,ksize=3)/8
 v=geo['vertices'][i];cam=d['cam'][i];tf=d['transforms'][i];proj=(v[:,:2]+cam[1:])*cam[0];proj[:,1]*=-1;proj=(proj+1)*112;src=np.column_stack([proj,np.ones(len(proj))])@np.linalg.inv(tf).T;pp=(src[:,:2]-center)*scale+256
 tri=v[ff];nf=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);nv=np.zeros_like(v)
 for k in range(3):np.add.at(nv,ff[:,k],nf)
 nv/=np.maximum(np.linalg.norm(nv,axis=1,keepdims=True),1e-8);norm=normbuffer(v,pp,ff,nv)
 # View-space bump: UV relief perturbs shading normals, not vertex positions.
 bump=norm.copy();bump[:,:,0]-=dx*1.5*valid;bump[:,:,1]+=dy*1.5*valid;bump/=np.maximum(np.linalg.norm(bump,axis=2,keepdims=True),1e-6)
 light=np.array([-.60,.45,.66]);light/=np.linalg.norm(light);half=light+np.array([0,0,1]);half/=np.linalg.norm(half)
 diffuse=np.maximum(0,norm@light);bumpdiff=np.maximum(0,bump@light)
 rough=.36-.17*gloss;exponent=2/rough**2-2
 spec=np.maximum(0,bump@half)**exponent
 lit=34+166*diffuse+10*np.maximum(0,norm@half)**28+14*(1-np.abs(norm[:,:,2]))**3
 effect=np.clip(147*(bumpdiff-diffuse),-12,12)*.7 -np.maximum(-height-.08,0)*5*valid
 old=frame[56:,512:].astype(np.float32);base=clean[i].astype(np.float32)
 keep=np.zeros((512,512),np.uint8)
 for region in [outer,le,re,lb,rb]:cv2.fillPoly(keep,[pts[region]],255)
 keep=cv2.dilate(keep,np.ones((5,5),np.uint8));protect=cv2.GaussianBlur(keep,(0,0),4)/255;skin=1-protect
 facevalid=cv2.GaussianBlur((base[:,:,0]>1).astype(np.float32),(0,0),1)
 clayweight=(.84*skin+.10*protect)*facevalid
 layer=old*(1-clayweight[:,:,None])+base*clayweight[:,:,None]
 lighting=(lit-base[:,:,0])*.84*skin*facevalid+effect*skin*facevalid
 # A clear coat across the clay plus stronger shine at the actual gloss-map locations.
 mouthmask=np.zeros((512,512),np.uint8);cv2.fillPoly(mouthmask,[pts[outer]],255)
 mouthmask=cv2.GaussianBlur(cv2.dilate(mouthmask,np.ones((5,5),np.uint8)),(0,0),3)/255
 allow=(1-mouthmask)*facevalid
 coat=58*np.maximum(0,bump@half)**30
 mapped_shine=65*gloss*spec
 shine=(coat+mapped_shine)*allow*(.45+.55*skin)
 layer+=lighting[:,:,None]+shine[:,:,None]
 # Very slight warm porcelain tint, applied only to the face.
 layer*=1+facevalid[:,:,None]*np.array([-.025,-.006,.012])
 layer=np.clip(layer,0,250).astype(np.uint8);ok,prev=previous.read();assert ok;before=prev[56:,512:].copy()
 for x,y in target:
  pos=(int(round(x*16)),int(round(y*16)))
  for img in [layer]:cv2.circle(img,pos,16,(65,245,155),-1,cv2.LINE_AA,shift=4)
 for idx,(o,s) in enumerate(writers):
  canvas=np.zeros((568,1024,3),np.uint8);canvas[56:,:512]=frame[56:,:512] if idx==0 else before;canvas[56:,512:]=layer
  for j,t in enumerate(['SOURCE' if idx==0 else 'DETAILED BASE','SCULPTED 3D + RELIEF + GLOSS']):cv2.putText(canvas,t,(j*512+12,35),0,.5,(235,235,235),1,cv2.LINE_AA)
  vf=av.VideoFrame.from_ndarray(canvas,format='bgr24');vf.pts=i;vf.time_base=Fraction(1,30)
  for pk in s.encode(vf):o.mux(pk)
  if i in [15,90,172] and idx==1:cv2.imwrite(str(O/f'Before-after-{i:03d}.jpg'),canvas)
 stats.append({'frame':i,'bump_p95_luma':float(np.percentile(abs(effect[valid>.5]),95)),'added_shine_p95':float(np.percentile(shine[facevalid>.8],95)),'map_shine_max':float(np.max(mapped_shine*allow))})
 if i%60==0:print('Rendered',i,flush=True)
for o,s in writers:
 for pk in s.encode():o.mux(pk)
 o.close()
cap.release();previous.release();ffmpeg=executable('ffmpeg');audio=str(root/'Original-and-detailed-mesh.mp4')
for src,name in [('sculpted-source-silent','Original-and-sculpted-3D.mp4'),('sculpted-before-after-silent','Detailed-vs-sculpted-3D.mp4')]:
 subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-y','-i',str(P/(src+'.mp4')),'-i',audio,'-map','0:v:0','-map','1:a:0?','-c','copy','-movflags','+faststart',str(O/name)],check=True)
subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-y','-i',str(O/'Original-and-sculpted-3D.mp4'),'-vf','crop=512:512:512:56','-c:v','libx264','-threads','4','-crf','15','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(O/'Sculpted-3D-mask.mp4')],check=True)
report={}
for path in O.glob('*.mp4'):
 r=json.loads(subprocess.check_output([executable('ffprobe'),'-v','error','-show_entries','stream=codec_type,width,height,nb_frames,duration,r_frame_rate','-of','json',str(path)]));vid=next(z for z in r['streams'] if z['codec_type']=='video');assert int(vid['nb_frames'])==N and vid['r_frame_rate']=='30/1';assert (not CFG['has_audio']) or any(z['codec_type']=='audio' and abs(float(z['duration'])-N/30)<.1 for z in r['streams']);report[path.name]=r
(O/'Validation.json').write_text(json.dumps(report,indent=2));(O/'Map-effect-stats.json').write_text(json.dumps(stats,indent=2));(O/'Read-me.txt').write_text(f'SCULPTED 3D + CREASE TEST: {N} frames at 30fps; source audio if present.\n\nUses exact UV relief and gloss sequences from '+str(R)+'. Maps 0000–0643 are sampled through canonical OBJ UV triangles onto approved tracked crop coordinates. Source out-of-frame triangles excluded; eyes/mouth holes excluded from relief. Normal perturbations are view-space bump shading, not vertex displacement. Gloss modulates roughness (0.36 to 0.19), with stronger map-gated specular highlights plus an overall clay clear coat. Eyes included in gloss projection; mouth/teeth excluded from added shine. Luminance-derived relief may include lighting; it is not measured physical depth.\n\nSkin blends 84% clay with stronger directional light; key expression areas 10%. Small warm tint and directional light. Original approved geometry and landmark points unchanged. Detailed source eye/mouth appearance retained.\n')
shutil.copy2(__file__,O/'render-sculpted-3d.py');print('DONE; 3 exports validated',flush=True)
