"""Generate and audit a bounded WedgeOrder preflight dataset.

This is diagnostic evidence only. It is intentionally separate from any future
prepare.py, grader, or release dataset.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


SIZE = 128
N_WEDGES = 8
PAIRS = [(i, j) for i in range(N_WEDGES) for j in range(i + 1, N_WEDGES)]
OVERLAP_PIXELS = 24
PROFILE_SEPARATION = 0.035


def smooth_noise(rng: np.random.Generator, size: int) -> np.ndarray:
    small = rng.normal(0, 1, (16, 16)).astype(np.float32)
    lo = float(small.min())
    hi = float(small.max())
    arr = ((small - lo) * (255.0 / max(hi - lo, 1e-6))).astype(np.uint8)
    image = Image.fromarray(arr).resize((size, size), Image.Resampling.BICUBIC)
    image = image.filter(ImageFilter.GaussianBlur(radius=2.2))
    out = np.asarray(image, dtype=np.float32) / 255.0
    return out - float(out.mean())


def wedge_fields(param: np.ndarray, yy: np.ndarray, xx: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    cy, cx, angle, scale = [float(v) for v in param]
    ca, sa = math.cos(angle), math.sin(angle)
    dx, dy = xx - cx, yy - cy
    u = dx * ca + dy * sa
    v = -dx * sa + dy * ca
    length = 28.0 * scale
    width = 10.0 * scale
    t = (u / length) + 0.38
    half = width * np.clip(1.02 - 0.72 * t, 0.22, 1.05)
    core = (t >= 0.0) & (t <= 1.0) & (np.abs(v) <= half)
    expanded = (t >= -0.07) & (t <= 1.07) & (np.abs(v) <= half + 2.2 * scale)
    cross = np.clip(1.0 - (v / np.maximum(half, 1e-3)) ** 2, 0.0, 1.0)
    head = np.exp(-((t - 0.12) / 0.24) ** 2)
    tail = np.clip(1.0 - t, 0.08, 1.0)
    depression = (0.48 + 0.52 * head) * cross * tail
    profile = -depression.astype(np.float32)
    return core, expanded, profile


def render_relief(height: np.ndarray, base_color: np.ndarray, lights: np.ndarray, gamma: float) -> np.ndarray:
    gy, gx = np.gradient(height)
    normal = np.stack((-gx * 7.0, -gy * 7.0, np.ones_like(height)), axis=-1)
    normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-6)
    panels = []
    clay_rgb = np.array([0.78, 0.57, 0.39], dtype=np.float32)
    view = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    for light in lights:
        light = light / np.linalg.norm(light)
        diffuse = np.clip(np.sum(normal * light[None, None, :], axis=-1), 0.0, 1.0)
        half_vec = light + view
        half_vec /= np.linalg.norm(half_vec)
        specular = np.clip(np.sum(normal * half_vec[None, None, :], axis=-1), 0.0, 1.0) ** 18
        intensity = np.clip(base_color * (0.20 + 0.86 * diffuse) + 0.10 * specular, 0.0, 1.0)
        rgb = np.clip(intensity[..., None] * clay_rgb[None, None, :], 0.0, 1.0) ** gamma
        panels.append((rgb * 255.0 + 0.5).astype(np.uint8))
    return np.concatenate(panels, axis=1)


def make_scene(rng: np.random.Generator, recipe: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    params: list[list[float]] = []
    for k in range(N_WEDGES):
        if k == 0 or rng.random() < 0.22:
            cy, cx = rng.uniform(25, 103, 2)
        else:
            anchor = params[int(rng.integers(0, len(params)))]
            radius = rng.uniform(10, 24)
            theta = rng.uniform(0, 2 * math.pi)
            cy = np.clip(anchor[0] + radius * math.sin(theta), 20, 108)
            cx = np.clip(anchor[1] + radius * math.cos(theta), 20, 108)
        angle = rng.choice([0, math.pi / 4, math.pi / 2, 3 * math.pi / 4]) + rng.normal(0, 0.09)
        scale = rng.uniform(0.78, 1.18)
        params.append([float(cy), float(cx), float(angle), float(scale)])

    # IDs are observable: top-to-bottom, then left-to-right in the supplied plan.
    params_arr = np.asarray(sorted(params, key=lambda p: (p[0], p[1])), dtype=np.float32)
    fields = [wedge_fields(p, yy, xx) for p in params_arr]
    order = rng.permutation(N_WEDGES)
    rank = np.empty(N_WEDGES, dtype=np.int8)
    rank[order] = np.arange(N_WEDGES, dtype=np.int8)

    texture = smooth_noise(rng, SIZE)
    base = 0.055 * texture
    curved = recipe in {"curved", "combined"}
    worn = recipe in {"worn", "combined"}
    oblique = recipe in {"oblique", "combined"}
    if curved:
        yc, xc = rng.uniform(45, 83, 2)
        base += rng.uniform(-0.08, 0.08) * (((xx - xc) / SIZE) ** 2 + ((yy - yc) / SIZE) ** 2)
    height = base.copy()
    profiles: list[np.ndarray] = []
    for idx in order:
        core, expanded, raw_profile = fields[int(idx)]
        depth = rng.uniform(0.24, 0.42)
        target = base + depth * raw_profile
        # Later impressions replace most of the earlier surface inside the stylus footprint.
        height[core] = 0.12 * height[core] + 0.88 * target[core]
        ring = expanded & ~core
        height[ring] += depth * 0.10 * (1.0 + texture[ring])
        profiles.append(target)

    if worn:
        as_u8 = np.clip((height - height.min()) / max(float(np.ptp(height)), 1e-6) * 255, 0, 255).astype(np.uint8)
        blurred = np.asarray(Image.fromarray(as_u8).filter(ImageFilter.GaussianBlur(radius=0.75)), dtype=np.float32)
        blurred = blurred / 255.0 * float(np.ptp(height)) + float(height.min())
        height = 0.72 * height + 0.28 * blurred + rng.normal(0, 0.006, height.shape)

    labels = np.zeros(len(PAIRS), dtype=np.int8)
    visible_support = []
    for pidx, (i, j) in enumerate(PAIRS):
        overlap = fields[i][0] & fields[j][0]
        count = int(overlap.sum())
        if count < OVERLAP_PIXELS:
            continue
        pi = base + 0.33 * fields[i][2]
        pj = base + 0.33 * fields[j][2]
        separation = float(np.mean(np.abs(pi[overlap] - pj[overlap])))
        if separation < PROFILE_SEPARATION:
            continue
        labels[pidx] = 1 if rank[i] > rank[j] else 2
        visible_support.append({"i": i, "j": j, "pixels": count, "profile_separation": separation})

    azimuths = np.deg2rad(np.array([25.0, 145.0, 265.0]) + rng.uniform(-18, 18))
    if oblique:
        elevations = np.deg2rad(rng.uniform(18, 30, 3))
    else:
        elevations = np.deg2rad(rng.uniform(34, 52, 3))
    lights = np.stack(
        [np.cos(elevations) * np.cos(azimuths), np.cos(elevations) * np.sin(azimuths), np.sin(elevations)],
        axis=1,
    )
    clay = np.clip(0.68 + 0.18 * texture + rng.normal(0, 0.015, texture.shape), 0.30, 0.95)
    image = render_relief(height.astype(np.float32), clay.astype(np.float32), lights.astype(np.float32), rng.uniform(0.86, 1.18))
    if worn:
        image = np.asarray(Image.fromarray(image).filter(ImageFilter.GaussianBlur(radius=0.35)))

    # Quantized/noisy plan: center, orientation and scale; enough to identify IDs and candidate contacts,
    # but not the per-scene clay response or application order.
    plan = params_arr.copy()
    plan[:, :2] = np.round((plan[:, :2] + rng.normal(0, 0.7, (N_WEDGES, 2))) / (SIZE - 1), 3)
    plan[:, 2] = np.round(plan[:, 2] / math.pi, 3)
    plan[:, 3] = np.round(plan[:, 3] + rng.normal(0, 0.025, N_WEDGES), 3)
    meta = {"recipe": recipe, "order": order.tolist(), "scored_edges": int(np.count_nonzero(labels)), "support": visible_support, "exact_plans": params_arr.tolist()}
    return image, plan.astype(np.float32), labels, meta

