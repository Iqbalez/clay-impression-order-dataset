# Simulated Clay Impression Contacts

This repository is the primary source and provenance page for the **Clay Impression Order** CPU challenge dataset, version 3.0. The dataset contains 1,600 original simulated clay surfaces, with ten stylus impressions and three raking-light views per surface. All images, measured plans and contact annotations are creator-generated. No external archaeological photograph, mesh or scan is used.

## Creation process

`renderer.py` samples stylus geometry, application order, a textured clay height field, individual impression depths and illumination. Impressions successively overwrite relief and add a small raised rim. `generate.py` creates the frozen corpus using independent per-scene random streams. Each RGB image is 128 x 384 pixels, combining three registered 128 x 128 views.

There are 200 scenes in each individual acquisition recipe (clean, curved, worn and oblique-light), plus 800 combined-condition scenes. The orientation distribution is identical in training and evaluation. The challenge's preparation script reserves the 800 combined-condition scenes for evaluation and derives directed overlap relations from exact geometry and application order. Training contains 800 scenes, with a prescribed training-only validation partition of 160 scenes (640 core scenes).

The raw dataset is `scenes.npz`. Its exact size and SHA-256 are recorded in `release_manifest.json`; that manifest identifies the data used by the challenge. This repository publishes the generator and provenance, not evaluation truth, scene entropy, or a searchable answer index. The platform distributes the prepared participant files.

## Raw schema

| Array | Shape | Dtype | Meaning |
|---|---|---|---|
| images | 1600 x 128 x 384 x 3 | uint8 | Final surface observations |
| plans | 1600 x 10 x 4 | float32 | Measured centers, orientation and scale |
| exact_plans | 1600 x 10 x 4 | float32 | Creator-side exact geometry |
| orders | 1600 x 10 | uint8 | Creator-side application sequences |
| recipes | 1600 | uint8 | Acquisition conditions, 0..4 |

The creator-side fields are used by `prepare.py` and are not public solver features. A directed edge `a>b` means impression a was applied later than b at a qualifying contact (at least 24 interior overlap pixels and mean nominal profile separation 0.035 at depth 0.33). The target is a partial contact chronology, not a total ordering, transliteration or sign class.

## License

Original generated data and annotations: **CC0 1.0 Universal**, see `DATA_LICENSE.txt` and https://creativecommons.org/publicdomain/zero/1.0/ . Implementation: **MIT**, see `LICENSE`.

## Intended use and limitations

The intended use is benchmarking CPU feature engineering and structured visual reasoning for final-surface contact chronology. These are dimensionless height-field simulations, not validated physical clay models or historical measurements. There are ten impressions with continuous full-turn orientations, a fixed camera, registered light views and a supplied measured plan. The dataset does not cover actual sign inventories, languages, scribes, fractures, perspective variation or full plastic deformation. Later impressions can obscure earlier contacts. Generalization to real artifacts is unmeasured.

Related context, not redistributed source data: [W3Dge physical writing series](https://zenodo.org/records/20608307) and [cuneiform sign detection](https://arxiv.org/abs/2308.11277). W3Dge supplies intermediate physical 3D scans; this task supplies final simulated observations and evaluates a directed contact graph.

## Generating a separate research corpus

Install the dependencies in `requirements.txt` in an isolated environment, then run:

```sh
python generate.py --out research/raw --entropy-file private_entropy.hex --per-recipe 200 --test-scenes 800 --batch-limit 1600
```

The command above generates all 1,600 scenes. For incremental generation, use `--batch-limit 400` and repeat the same command four times; it resumes using the same entropy. A newly created entropy file produces a different corpus; it cannot reproduce the challenge's private scene realizations. Retain it privately when exact regeneration of your own corpus is needed. Reproducing challenge **preparation** instead uses the frozen uploaded raw file and deterministic `prepare.py`.

## Release history

Version 3.0 uses ten impressions, continuous orientations and 800 training / 800 evaluation scenes. The earlier eight-impression version remains in Git history and is superseded for new uploads. `release_manifest.json` identifies the current raw dataset; files from different versions must not be mixed.
