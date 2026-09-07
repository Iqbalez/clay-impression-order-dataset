# Simulated Clay Process Changes

This creator-generated dataset supports **Clay Process Change**, an offline CPU benchmark for predicting the spatial effect of exchanging two press operations in a hidden sequence. It contains 2,200 independent simulated surfaces, each with ten stylus impressions, one three-light final observation, a measured footprint plan and one intervention query. It is intended for research on inverse process reasoning and counterfactual material-change localization.

## Creation and provenance

An original NumPy/Pillow/SciPy generator samples tool geometry, continuous full-turn orientations, press depths, application order, base texture and illumination. A height-field process applies each impression, mixing 12% of the previous core relief with 88% of the new nominal profile and adding a small surrounding rim. Three registered raking-light renderings of the final surface form a 128-by-384 RGB image. The footprint plan includes modest measurement uncertainty and rounding.

A query names two geometrically overlapping tools. Original scenes select the query without inspecting application order; the diagnostic supplement conditions query selection on contact visibility derived from geometry and order. Neither process selects by intervention outcome or model performance. The factual and counterfactual processes share every material variable; the counterfactual exchanges the two named operations' positions. `prepare.py` independently replays both histories from creator raw variables and derives a signed 128-by-128 change mask. The target marks height differences above +0.02 or below -0.02 after rounding to six decimals. Small differences form the unchanged class. No counterfactual image is released to solvers.

The data are wholly synthetic and original. No archaeological photograph, mesh, writing corpus, font or third-party observation is redistributed. Generated observations and annotations are **CC0 1.0 Universal**; implementation is **MIT**. The primary source is [the creator's dataset repository](https://github.com/Iqbalez/clay-impression-order-dataset), whose version 4.1 manifest records the exact raw file hash and generator hashes. This repository preserves prior versions in Git history; the current process-change dataset must not be mixed with the earlier contact-graph release. [CC0 license](https://creativecommons.org/publicdomain/zero/1.0/).

## Raw files and schema

The raw upload contains only `scenes.npz` and `LICENSE.txt` at the archive root. The NumPy file loads with `allow_pickle=False`:

| Array | Shape | Type | Purpose |
|---|---|---|---|
| images | 2200 x 128 x 384 x 3 | uint8 | Final factual three-light observations. |
| plans | 2200 x 10 x 4 | float32 | Measured normalized centers, angle/pi and scale. |
| queries | 2200 x 2 | uint8 | Two tool IDs whose sequence positions are exchanged. |
| exact_plans | 2200 x 10 x 4 | float32 | Private centers in pixels, angles in radians and scales. |
| orders | 2200 x 10 | uint8 | Private application sequences, earliest first. |
| depths | 2200 x 10 | float32 | Private press depths indexed by tool ID. |
| textures | 2200 x 128 x 128 | float32 | Private material texture used in paired replay. |
| recipes | 2200 | uint8 | Private acquisition condition, 0 through 4. |
| tracks | 2200 | uint8 | Private provenance: 0 original sampling, 1 visibility-conditioned supplement. |

Raw hidden variables are supplied to the platform solely for deterministic preparation and must not be exposed as participant files. Private entropy is retained separately by the creator and is not uploaded or published. Reproducing preparation requires only this frozen raw upload, not the entropy or internet access.

## Prepared data and splits

The original 1,600 scenes are retained byte-for-byte: 200 in each individual condition (clean, curved, worn, oblique light), providing 800 training observations, plus 800 combined-condition evaluation observations. The diagnostic amendment adds 600 fresh combined-condition evaluation scenes, 200 in each of three physical visibility categories. Final counts are 2,200 scenes: 800 train and 1,400 evaluation. Within each training condition, every fifth content-ID-sorted scene is validation (640 core / 160 validation). Existing training files and the original evaluation targets are unchanged.

For a query pair, visibility is the fraction of its exact core intersection not covered by cores of other presses applied after both queried operations. Zero visible pixels defines fully occluded contact; all visible defines exposed; intermediate values define partial occlusion. This is geometric coverage by later material operations, not a guarantee that all residual height signal disappears. The natural evaluation cohort sizes are 436 exposed, 330 partial and 34 fully occluded. A separate supplement adds 200 per category, each from a distinct scene.

The supplement conditions on a qualifying pair's physical visibility only, without checking model errors or whether the intervention causes any labeled change. Of 200/205/437 independently sampled candidate scenes, respectively, 200 were accepted for exposed/partial/fully-occluded groups. No accepted scene is reused across queries or splits. The conditioned distribution must not be interpreted as natural prevalence. The raw track flag lets preparation and the creator report distinguish these populations; it is not a solver feature.

Preparation rejects duplicate images and latent layouts, is invariant to raw row order, and assigns all public/private splits and diagnostic annotations itself. Hidden evaluation groups go to private `test_diagnostics.csv`; training groups go to public `train_diagnostics.csv`. Group-specific F1, 95% scene-bootstrap intervals, sample counts and unchanged-target rates accompany the unchanged official per-scene metric.

`train.csv` and `test.csv` share exactly `case_id,image_path,plan,swap_a,swap_b`. Training labels are separate in `train_labels.csv`; both labels and private `answers.csv` use exactly `case_id,change_mask`, matching `sample_submission.csv`. `train_groups.csv` records the training-only partition. The public images directory contains 2,200 PNGs. The sample uses the explicit full unchanged mask `0:16384`, with no blank or null-like placeholder.

Masks use canonical row-major `class:length` run-length encoding, covering 16,384 pixels, with classes 0 unchanged, 1 raised and 2 lowered. Evaluation uses mean per-scene signed foreground F1. It rewards correctly located changes with the correct sign, and does not reward the large unchanged background.

## Related work and material differences

- [W3Dge](https://zenodo.org/records/20608307) records physical impression sequences through stepwise 3D scans and labels. This dataset instead has synthetic terminal observations and paired outcomes for an explicit change to operation order; neither intermediate scans nor the factual chronology are solver inputs.
- [OcclusionFormer/SA-Z](https://arxiv.org/abs/2605.21343) addresses occlusion-aware image generation with supplied order and amodal layouts. The output here is a signed effect field of a material process, which depends on press depths and intervening operations as well as order.
- [CoPhy](https://projet.liris.cnrs.fr/cophy/) and [ObjectDrop](https://research.google/pubs/objectdrop-bootstrapping-counterfactuals-for-photorealistic-object-removal-and-insertion/) establish related counterfactual physics and image-editing tasks. Our observations contain only the terminal relief, and the intervention exchanges past operations rather than editing a present object or an initial configuration.
- [FactoryBench](https://arxiv.org/abs/2605.07675) covers causal question answering over machine telemetry. Here the evidence and scored answer are spatial surface observations and paired-simulation masks.

The diagnostic amendment makes a specific comparison possible: terminal-surface inference when the queried contact remains exposed versus when later presses cover it, with acquisition conditions held the same and independent scene counts stated. Neither prior-art similarity nor a diagnostic score is itself proof of a novelty rating.

These are prior-art citations, not data sources. The comparison is scoped to the cited works and does not claim exhaustive absence of related research.

## Known limitations

This is a dimensionless height-field overwrite model, not a validated physical model of real clay or industrial forming. There are exactly ten operations from one stylus-profile family, a fixed camera and registered lighting panels. The benchmark does not include real scripts, historical manufacturing claims, full plastic flow, fractures, perspective errors or impression detection without a plan. Some hidden histories can produce similar observations and uncertain intervention outcomes. The split tests a particular combination of simulation conditions; transfer to real objects and other tools is unmeasured. The data contain no personal records or sensitive human fields. IDs carry no application-order information.


## Generate a separate research corpus

Install requirements.txt, then run:

```sh
python generate.py --out research/raw --entropy-file private_entropy.hex --per-cohort 200
```

This generates an independent 1,600-scene base and appends 200 new scenes per contact-visibility group. To retain an existing version-4 base, add `--base-raw path/to/version4/scenes.npz`. The frozen release used the original version-4 raw file, identified by its hash in the manifest. New private entropy creates different supplement scenes; preserve it separately for research reproducibility. Never use additional generated training data in the platform challenge. The generator refuses to overwrite an existing scenes.npz. Preparation uses the frozen raw upload and needs neither entropy nor internet access.

The generator's local provenance files include attempt indices and generation counts. The platform raw ZIP contains only scenes.npz and LICENSE.txt. This source repository publishes eight source, license and provenance files; no frozen observations, evaluation labels, attempt indices or private entropy are published.

## Release history

Version 4.1 retains all version-4 data and adds 600 independent visibility-conditioned evaluation scenes, a private track array, and deterministic contact-visibility diagnostics. It preserves the signed-mask target and official scoring formula. Version 4.0 introduced process-order intervention effects; its source is preserved at commit dd4f668565bc63d57c00821f6fb3db06d2563d7b. Version 3.0 was a factual contact-graph task preserved at eb27287e3e3b5480d2553558666e88d43cd67580. Their raw schemas and targets must not be mixed.
