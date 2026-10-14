import numpy as np
from numba import njit
@njit
def raster(v,xy,faces,norms):
 im=np.zeros((512,512,3),np.uint8);zb=np.full((512,512),-1e10)
 for ids in faces:
  a,b,c=xy[ids[0]],xy[ids[1]],xy[ids[2]]
  x0=max(0,int(np.floor(min(a[0],b[0],c[0]))));x1=min(511,int(np.ceil(max(a[0],b[0],c[0]))))
  y0=max(0,int(np.floor(min(a[1],b[1],c[1]))));y1=min(511,int(np.ceil(max(a[1],b[1],c[1]))))
  den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-8:continue
  for y in range(y0,y1+1):
   for x in range(x0,x1+1):
    wa=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
    wb=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;wc=1-wa-wb
    if min(wa,wb,wc)<-0.001:continue
    z=wa*v[ids[0],2]+wb*v[ids[1],2]+wc*v[ids[2],2]
    if z<zb[y,x]:continue
    n=wa*norms[ids[0]]+wb*norms[ids[1]]+wc*norms[ids[2]];n=n/max(np.sqrt((n*n).sum()),1e-9)
    diff=max(0,(-.25*n[0]+.35*n[1]+n[2])/1.09);s=min(255,40+160*diff+15*max(0,n[2])**24)
    im[y,x,:]=s;zb[y,x]=z
 return im