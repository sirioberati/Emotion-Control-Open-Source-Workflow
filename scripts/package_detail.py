from common import executable
from common import CFG,WORK,N
import subprocess
subprocess.run([executable('ffmpeg'),'-hide_banner','-loglevel','error','-y','-i',str(WORK/'full-test/Detail-assisted-test-silent.mp4'),'-i',CFG['video'],'-filter_complex','[0:v]split[a][b];[a]crop=512:568:0:0[l];[b]crop=512:568:1024:0[r];[l][r]hstack=inputs=2[v]','-map','[v]','-map','1:a:0?','-t',str(N/30),'-c:v','libx264','-threads','4','-crf','16','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(WORK/'full-test/Original-and-detailed-mesh.mp4')],check=True)
