"""Create original simulated observations; the entropy file is creator-private."""
import argparse
import hashlib
import json
import secrets
import time
from pathlib import Path
import numpy as np
from renderer import make_scene

RECIPES = ['clean', 'curved', 'worn', 'oblique', 'combined']

def generate(out, entropy_file, per_recipe=800, batch_limit=400):
    out, entropy_file = Path(out), Path(entropy_file)
    out.mkdir(parents=True, exist_ok=True)
    entropy_file.parent.mkdir(parents=True, exist_ok=True)
    if not entropy_file.exists():
        entropy_file.write_text(secrets.token_hex(32), encoding='ascii')
    entropy = bytes.fromhex(entropy_file.read_text(encoding='ascii').strip())
    if len(entropy) != 32:
        raise ValueError('entropy file must contain 32 bytes as hexadecimal')
    n = per_recipe * 5
    scratch=out/'.generation'
    scratch.mkdir(exist_ok=True)
    image_file=scratch/'images.npy'
    progress_file=scratch/'progress.json'
    resume=json.loads(progress_file.read_text()) if progress_file.exists() else {'completed':0,'metadata':[],'counts':[]}
    if resume.get('entropy_hash',hashlib.sha256(entropy).hexdigest())!=hashlib.sha256(entropy).hexdigest():
        raise ValueError('resume entropy does not match')
    images=np.lib.format.open_memmap(image_file,mode='r+' if image_file.exists() else 'w+',dtype=np.uint8,shape=(n,128,384,3))
    plans = np.empty((n,8,4),dtype=np.float32)
    exact = np.empty_like(plans)
    orders = np.empty((n,8),dtype=np.uint8)
    recipes = np.repeat(np.arange(5,dtype=np.uint8),per_recipe)
    start = time.perf_counter()
    counts=resume['counts']
    metadata=resume['metadata']
    for k,item in enumerate(metadata):
        plans[k],exact[k],orders[k]=item['plan'],item['exact'],item['order']
    for k, recipe_id in enumerate(recipes):
        if k<resume['completed']:continue
        seed=hashlib.sha256(entropy+k.to_bytes(8,'big')).digest()
        rng=np.random.default_rng(int.from_bytes(seed,'big'))
        im, plan, y, meta = make_scene(rng, RECIPES[int(recipe_id)])
        images[k],plans[k],exact[k],orders[k]=im,plan,meta['exact_plans'],meta['order']
        counts.append(meta['scored_edges'])
        metadata.append({'plan':plan.tolist(),'exact':meta['exact_plans'],'order':meta['order']})
        if (k+1)%50==0:
            images.flush()
            progress={'completed':k+1,'metadata':metadata,'counts':counts,'entropy_hash':hashlib.sha256(entropy).hexdigest()}
            temp=progress_file.with_suffix('.tmp')
            temp.write_text(json.dumps(progress),encoding='utf8');temp.replace(progress_file)
        if (k+1)%200==0:
            print(f'Generated {k+1}/{n} scenes in {time.perf_counter()-start:.1f}s',flush=True)
        if k+1<n and k+1-resume['completed']>=batch_limit and (k+1)%50==0:
            print('Batch saved; run the same command to continue.',flush=True)
            return
    file=out/'scenes.npz'
    np.savez_compressed(file,images=images,plans=plans,exact_plans=exact,orders=orders,recipes=recipes)
    report={'status':'MEASURED','scenes':n,'per_recipe':per_recipe,'recipes':RECIPES,
            'zero_edge_scenes':counts.count(0),'edge_count':sum(counts),'minimum_edges':min(counts),
            'seconds':time.perf_counter()-start,'raw_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
            'raw_bytes':file.stat().st_size,'numpy':np.__version__,
            'entropy_policy':'256-bit creator-private entropy. Never include the entropy file in a public release.'}
    report_dir=out.parent.parent/'reports'
    report_dir.mkdir(parents=True,exist_ok=True)
    (report_dir/'generation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--entropy-file',type=Path,required=True)
    p.add_argument('--per-recipe',type=int,default=800)
    p.add_argument('--batch-limit',type=int,default=400)
    a=p.parse_args()
    generate(a.out,a.entropy_file,a.per_recipe,a.batch_limit)
