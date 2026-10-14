"""Regenerate the silent, looping README GIFs from included MP4s."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
for source,name,start,width,duration in [
 ('videos/courtroom-preview.mp4','courtroom',0,480,None),
 ('videos/emotional-performance.mp4','emotional',2,480,6),
 ('videos/expressive-original.mp4','expressive-original',2,480,6),
 ('videos/expressive-sirio.mp4','expressive-sirio',2,480,6),
 ('masks/expressive-mask.mp4','expressive-mask',2,400,6),
 ('masks/emotional-mask.mp4','emotional-mask',6,400,10),
]:
 output=ROOT/'examples/previews'/f'{name}.gif'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(start),*(['-t',str(duration)] if duration is not None else []),'-i',str(ROOT/'examples'/source),'-filter_complex',f'fps=10,scale={width}:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a','-loop','0',str(output)],check=True)
 print(output.name,round(output.stat().st_size/1048576,2),'MiB',flush=True)
