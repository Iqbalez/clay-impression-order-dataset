# Simulated Clay Process Changes

This creator-generated dataset supports **Clay Process Change**, an offline CPU benchmark for predicting the spatial effect of exchanging two press operations in a hidden sequence. It contains 1,600 independent simulated surfaces, each with ten stylus impressions, one three-light final observation, a measured footprint plan and one intervention query. It is intended for research on inverse process reasoning and counterfactual material-change localization.

## Creation and provenance

An original NumPy/Pillow/SciPy generator samples tool geometry, continuous full-turn orientations, press depths, application order, base texture and illumination. A height-field process applies each impression, mixing 12% of the previous core relief with 88% of the new nominal profile and adding a small surrounding rim. Three registered raking-light renderings of the final surface form a 128-by-384 RGB image. The footprint plan includes modest measurement uncertainty and rounding.

A query names two geometrically overlapping tools, selected without inspecting their order or intervention outcome. The factual and counterfactual processes share every material variable; the counterfactual exchanges the two named operations' positions. `prepare.py` independently replays both histories from creator raw variables and derives a signed 128-by-128 change mask. The target marks height differences above +0.02 or below -0.02 after rounding to six decimals. Small differences form the unchanged class. No counterfactual image is released to solvers.

The data are wholly synthetic and original. No archaeological photograph, mesh, writing corpus, font or third-party observation is redistributed. Generated observations and annotations are **CC0 1.0 Universal**; implementation is **MIT**. The primary source is [the creator's dataset repository](https://github.com/Iqbalez/clay-impression-order-dataset), whose version 4 manifest records the exact raw file hash and generator hashes. This repository preserves prior versions in Git history; the current process-change dataset must not be mixed with the earlier contact-graph release. [CC0 license](https://creativecommons.org/publicdomain/zero/1.0/).

## Raw files and schema

The raw upload contains only `scenes.npz` and `LICENSE.txt` at the archive root. The NumPy file loads with `allow_pickle=False`:

| Array | Shape | Type | Purpose |
|---|---|---|---|
| images | 1600 x 128 x 384 x 3 | uint8 | Final factual three-light observations. |
| plans | 1600 x 10 x 4 | float32 | Measured normalized centers, angle/pi and scale. |
| queries | 1600 x 2 | uint8 | Two tool IDs whose sequence positions are exchanged. |
| exact_plans | 1600 x 10 x 4 | float32 | Private centers in pixels, angles in radians and scales. |
| orders | 1600 x 10 | uint8 | Private application sequences, earliest first. |
| depths | 1600 x 10 | float32 | Private press depths indexed by tool ID. |
| textures | 1600 x 128 x 128 | float32 | Private material texture used in paired replay. |
| recipes | 1600 | uint8 | Private acquisition condition, 0 through 4. |

Raw hidden variables are supplied to the platform solely for deterministic preparation and must not be exposed as participant files. Private entropy is retained separately by the creator and is not uploaded or published. Reproducing preparation requires only this frozen raw upload, not the entropy or internet access.

## Prepared data and splits

There are 200 scenes in each individual condition (clean, curved, worn, oblique light) and 800 combined-condition scenes. The individual conditions form 800 training observations; the combined condition supplies 800 evaluation observations. Within each training condition, every fifth content-ID-sorted scene is validation: 640 core and 160 validation total. Each independent scene has exactly one query; no multiple-view or intervention relatives cross splits. Preparation rejects repeated images and repeated latent layouts and is invariant to shuffled raw row order.

`train.csv` and `test.csv` share exactly `case_id,image_path,plan,swap_a,swap_b`. Training labels are separate in `train_labels.csv`; both labels and private `answers.csv` use exactly `case_id,change_mask`, matching `sample_submission.csv`. `train_groups.csv` records the training-only partition. The public images directory contains 1,600 PNGs. The sample uses the explicit full unchanged mask `0:16384`, with no blank or null-like placeholder.

Masks use canonical row-major `class:length` run-length encoding, covering 16,384 pixels, with classes 0 unchanged, 1 raised and 2 lowered. Evaluation uses mean per-scene signed foreground F1. It rewards correctly located changes with the correct sign, and does not reward the large unchanged background.

## Related work and material differences

- [W3Dge](https://zenodo.org/records/20608307) records physical impression sequences through stepwise 3D scans and labels. This dataset instead has synthetic terminal observations and paired outcomes for an explicit change to operation order; neither intermediate scans nor the factual chronology are solver inputs.
- [OcclusionFormer/SA-Z](https://arxiv.org/abs/2605.21343) addresses occlusion-aware image generation with supplied order and amodal layouts. The output here is a signed effect field of a material process, which depends on press depths and intervening operations as well as order.
- [CoPhy](https://projet.liris.cnrs.fr/cophy/) and [ObjectDrop](https://research.google/pubs/objectdrop-bootstrapping-counterfactuals-for-photorealistic-object-removal-and-insertion/) establish related counterfactual physics and image-editing tasks. Our observations contain only the terminal relief, and the intervention exchanges past operations rather than editing a present object or an initial configuration.
- [FactoryBench](https://arxiv.org/abs/2605.07675) covers causal question answering over machine telemetry. Here the evidence and scored answer are spatial surface observations and paired-simulation masks.

These are prior-art citations, not data sources. The comparison is scoped to the cited works and does not claim exhaustive absence of related research.

## Known limitations

This is a dimensionless height-field overwrite model, not a validated physical model of real clay or industrial forming. There are exactly ten operations from one stylus-profile family, a fixed camera and registered lighting panels. The benchmark does not include real scripts, historical manufacturing claims, full plastic flow, fractures, perspective errors or impression detection without a plan. Some hidden histories can produce similar observations and uncertain intervention outcomes. The split tests a particular combination of simulation conditions; transfer to real objects and other tools is unmeasured. The data contain no personal records or sensitive human fields. IDs carry no application-order information.

## Generate a separate research corpus

Install requirements.txt, then run:

```sh
python generate.py --out research/raw --entropy-file private_entropy.hex --per-recipe 200 --test-scenes 800
```

New entropy creates different scenes. Keep it private for reproducibility; do not use extra generated training data in the platform challenge. The generator refuses to overwrite an existing scenes.npz. Challenge preparation uses the frozen raw upload and does not need entropy. This repository publishes eight source/provenance files; no frozen raw scenes, hidden targets or entropy are public.

## Release history

Version 4.0 changes the task to process-order intervention effects. Version 3.0 was a factual contact-graph task; its source remains at commit eb27287e3e3b5480d2553558666e88d43cd67580. These datasets have different targets and raw schemas. The manifest below identifies the current version.
