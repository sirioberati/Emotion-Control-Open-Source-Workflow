#!/usr/bin/env python3
"""Render a source video using Sirio's approved glossy sculpted-face workflow."""
import argparse,json,os,subprocess,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('video',type=Path);p.add_argument('--output',type=Path,required=True)
p.add_argument('--start',type=float,default=0);p.add_argument('--duration',type=float)
p.add_argument('--reuse-tracking',type=Path,help='Optional matching source-performance-geometry.npz in normalized source pixels')
p.add_argument('--map-project',type=Path,help='Optional project whose work/ contains matching UV maps and fused.npz')
p.add_argument('--identity-reference',type=Path,help='Optional 300-value shape array for matching a previously approved pilot of this same person')
p.add_argument('--resume',action='store_true');a=p.parse_args()
video=a.video.expanduser().resolve();out=a.output.expanduser().resolve();configpath=out/'Run-config.json';work=out/'_work'
if not video.is_file():p.error('Input video does not exist')
if configpath.exists() and not a.resume:p.error('Output already contains a run. Choose another folder or use --resume.')
if a.resume and configpath.exists():
 cfg=json.loads(configpath.read_text())
 if cfg['input']!=str(video):p.error('Resume input differs from saved run')
else:
 out.mkdir(parents=True,exist_ok=True);work.mkdir(exist_ok=True)
 cfg={'input':str(video),'output':str(out),'work':str(work),'start':a.start,'duration':a.duration,'reuse_tracking':str(a.reuse_tracking.resolve()) if a.reuse_tracking else None,'map_project':str(a.map_project.resolve()) if a.map_project else None,'identity_reference':str(a.identity_reference.resolve()) if a.identity_reference else None,'preset':'approved-sculpted-glossy-v1','fps':30}
 configpath.write_text(json.dumps(cfg,indent=2))
python=Path(sys.executable)
check=subprocess.run([str(python), str(ROOT/'tools/check_setup.py')])
if check.returncode:p.error('Setup is incomplete. See docs/SETUP.md.')
env=os.environ.copy();env['CAPTURE_CONFIG']=str(configpath);env['MPLCONFIGDIR']=str(work/'.mpl');env['PYTHONUNBUFFERED']='1'
log=out/'Run.log'
for name in ['prepare','infer','decode','fit','detail','package_detail','render']:
 stamp=work/(name+'.done')
 if a.resume and stamp.exists():print('Reuse completed stage:',name,flush=True);continue
 print('Running:',name,flush=True)
 with log.open('a') as f:
  f.write('\nSTAGE '+name+'\n');f.flush()
  result=subprocess.run([str(python),str(ROOT/'scripts'/f'{name}.py')],env=env,stdout=f,stderr=subprocess.STDOUT)
 if result.returncode:print('Stopped at '+name+'. See '+str(log),file=sys.stderr);sys.exit(result.returncode)
 stamp.write_text('complete\n')
print('Ready:',out/'Sculpted-3D-mask.mp4',flush=True)
