"""Create an independent raw corpus; private entropy never accompanies public source."""
import argparse,hashlib,json,secrets,time
from pathlib import Path
import numpy as np
from renderer import make_scene

def generate(out,entropy_file,per_recipe=200,test_scenes=800):
    out,entropy_file=Path(out),Path(entropy_file);out.mkdir(parents=True,exist_ok=True)
    if (out/'scenes.npz').exists():raise FileExistsError('Preserve frozen raw data; choose a new output directory')
    entropy_file.parent.mkdir(parents=True,exist_ok=True)
    if not entropy_file.exists():entropy_file.write_text(secrets.token_bytes(32).hex(),encoding='ascii')
    entropy=bytes.fromhex(entropy_file.read_text().strip())
    if len(entropy)!=32:raise ValueError('Expected 256-bit entropy')
    recipes=np.repeat(np.arange(5,dtype=np.uint8),[per_recipe]*4+[test_scenes]);n=len(recipes)
    data={'images':np.empty((n,128,384,3),np.uint8),'plans':np.empty((n,10,4),np.float32),
          'exact_plans':np.empty((n,10,4),np.float32),'orders':np.empty((n,10),np.uint8),
          'depths':np.empty((n,10),np.float32),'textures':np.empty((n,128,128),np.float32),
          'queries':np.empty((n,2),np.uint8),'recipes':recipes}
    start=time.perf_counter()
    for i,recipe in enumerate(recipes):
        seed=int.from_bytes(hashlib.sha256(entropy+i.to_bytes(8,'big')).digest()[:8],'big')
        image,plan,_,meta=make_scene(np.random.default_rng(seed),['clean','curved','worn','oblique','combined'][recipe])
        data['images'][i]=image;data['plans'][i]=plan
        for key,source in [('exact_plans','exact_plans'),('orders','order'),('depths','depths'),('textures','texture'),('queries','query')]:data[key][i]=meta[source]
        if i%200==0:print('Generated',i,'of',n,flush=True)
    raw=out/'scenes.npz';np.savez_compressed(raw,**data)
    report=dict(status='MEASURED',scenes=n,train=4*per_recipe,test=test_scenes,recipe_counts=[per_recipe]*4+[test_scenes],
                seconds=time.perf_counter()-start,raw_bytes=raw.stat().st_size,raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
                generator_sha256={name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in ['generate.py','renderer.py']})
    (out/'generation.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--entropy-file',required=True);p.add_argument('--per-recipe',type=int,default=200);p.add_argument('--test-scenes',type=int,default=800);a=p.parse_args();generate(a.out,a.entropy_file,a.per_recipe,a.test_scenes)
