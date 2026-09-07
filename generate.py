"""Create an independent raw corpus; private entropy never accompanies public source."""
import argparse,hashlib,json,secrets,time
from pathlib import Path
import numpy as np
from renderer import make_scene, wedge_fields

def generate_base(out,entropy_file,per_recipe=200,test_scenes=800):
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

def eligible_queries(exact,order):
    yy,xx=np.mgrid[:128,:128].astype(np.float32)
    masks=[wedge_fields(p,yy,xx)[0] for p in exact];rank=np.argsort(order)
    groups={name:[] for name in ['exposed_contact','partly_occluded_contact','fully_occluded_contact']}
    for a in range(10):
        for b in range(a+1,10):
            contact=masks[a]&masks[b];total=int(contact.sum())
            if total<24:continue
            later=np.zeros_like(contact)
            for j in range(10):
                if rank[j]>max(rank[a],rank[b]):later|=masks[j]
            visible=int((contact&~later).sum())
            name='fully_occluded_contact' if visible==0 else 'exposed_contact' if visible==total else 'partly_occluded_contact'
            groups[name].append((a,b))
    return groups

def generate(out,entropy_file,base_raw=None,per_cohort=200):
    out,entropy_file=Path(out),Path(entropy_file);out.mkdir(parents=True,exist_ok=True)
    if (out/'scenes.npz').exists():raise FileExistsError('Do not overwrite a frozen corpus')
    if base_raw is None:
        generate_base(out/'base_source',Path(str(entropy_file)+'.base'),200,800)
        base_raw=out/'base_source/scenes.npz'
    with np.load(base_raw,allow_pickle=False) as z:base={key:z[key] for key in z.files}
    if set(base)!={'images','plans','queries','exact_plans','orders','depths','textures','recipes'}:raise ValueError('Expected original version4 base corpus')
    entropy_file.parent.mkdir(parents=True,exist_ok=True)
    if not entropy_file.exists():entropy_file.write_text(secrets.token_bytes(32).hex(),encoding='ascii')
    entropy=bytes.fromhex(entropy_file.read_text().strip())
    if len(entropy)!=32:raise ValueError('Expected256-bit private entropy')
    extra={key:[] for key in base};accepted=[];seen={hashlib.sha256(x.tobytes()).hexdigest() for x in base['exact_plans']}
    attempts={};start=time.perf_counter();attempt=0
    for cohort in ['exposed_contact','partly_occluded_contact','fully_occluded_contact']:
        count=0;before=attempt
        while count<per_cohort:
            if attempt-before>20000:raise RuntimeError('Cohort rejection cap reached; preserve partial evidence')
            seed=int.from_bytes(hashlib.sha256(entropy+attempt.to_bytes(8,'big')).digest()[:8],'big');attempt+=1
            rng=np.random.default_rng(seed)
            image,plan,_,meta=make_scene(rng,'combined');exact=np.asarray(meta['exact_plans'],np.float32)
            choices=eligible_queries(exact,np.asarray(meta['order']))[cohort]
            if not choices:continue
            layout=hashlib.sha256(exact.tobytes()).hexdigest()
            if layout in seen:continue
            query=np.asarray(choices[int(rng.integers(len(choices)))],np.uint8);seen.add(layout)
            row=dict(images=image,plans=plan,queries=query,exact_plans=exact,orders=np.asarray(meta['order'],np.uint8),
                     depths=meta['depths'],textures=meta['texture'],recipes=np.uint8(4))
            for key,value in row.items():extra[key].append(value)
            accepted.append(dict(attempt_index=attempt-1,cohort=cohort));count+=1
        attempts[cohort]=attempt-before;print('Accepted',count,cohort,'from',attempts[cohort],'independent scenes',flush=True)
    data={key:np.concatenate([base[key],np.asarray(extra[key],dtype=base[key].dtype)]) for key in base}
    data['tracks']=np.r_[np.zeros(len(base['images']),np.uint8),np.ones(3*per_cohort,np.uint8)]
    raw=out/'scenes.npz';np.savez_compressed(raw,**data)
    report=dict(status='MEASURED',scenes=len(data['images']),train=int((data['recipes']<4).sum()),test=int((data['recipes']==4).sum()),
                original_scenes=len(base['images']),supplement_scenes=3*per_cohort,per_cohort=per_cohort,attempts=attempts,seconds=time.perf_counter()-start,
                base_raw_sha256=hashlib.sha256(Path(base_raw).read_bytes()).hexdigest(),raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),raw_bytes=raw.stat().st_size,
                selection='Conditioned only on exact geometry and history visibility; no outcome/model filtering')
    (out/'generation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    (out/'private_generation_indices.json').write_text(json.dumps(accepted),encoding='utf8')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--entropy-file',required=True);p.add_argument('--base-raw');p.add_argument('--per-cohort',type=int,default=200);a=p.parse_args()
    generate(a.out,a.entropy_file,a.base_raw,a.per_cohort)

