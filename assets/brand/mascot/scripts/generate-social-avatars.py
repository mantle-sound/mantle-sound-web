#!/usr/bin/env python3
"""Regenerate square social and avatar images (full mascot, not zoom-cropped)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

PNG = Path(__file__).resolve().parents[1] / "png"


def crop_to_ink(im: Image.Image, pad_ratio: float = 0.035) -> Image.Image:
    im = im.convert("RGBA")
    a = np.array(im)[:, :, 3]
    ys, xs = np.where(a > 0)
    if len(xs) == 0:
        return im
    y0, y1 = ys.min(), ys.max() + 1
    x0, x1 = xs.min(), xs.max() + 1
    pad = max(2, int(max(y1 - y0, x1 - x0) * pad_ratio))
    y0, x0 = max(0, y0 - pad), max(0, x0 - pad)
    y1, x1 = min(im.height, y1 + pad), min(im.width, x1 + pad)
    return im.crop((x0, y0, x1, y1))


def fit_square(im: Image.Image, size: int, bg: tuple[int, int, int], margin: float = 0.9) -> Image.Image:
    """Scale entire artwork to fit inside size×size (letterbox), centered."""
    im = crop_to_ink(im)
    w, h = im.size
    scale = min(size / w, size / h) * margin
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), bg + (255,))
    canvas.paste(im, ((size - nw) // 2, (size - nh) // 2), im)
    return canvas


def main() -> None:
    jobs: list[tuple[str, str, int, tuple[int, int, int]]] = [
        ("mascot-line-white-transparent.png", "mascot-social-black-1200.png", 1200, (0, 0, 0)),
        ("mascot-line-black-transparent.png", "mascot-social-white-1200.png", 1200, (255, 255, 255)),
        ("mascot-line-white-transparent.png", "mascot-avatar-black-512.png", 512, (0, 0, 0)),
        ("mascot-line-black-transparent.png", "mascot-avatar-white-512.png", 512, (255, 255, 255)),
    ]
    for src_name, dest_name, size, bg in jobs:
        src = PNG / src_name
        if not src.is_file():
            print("skip missing", src_name)
            continue
        out = fit_square(Image.open(src), size, bg)
        out.convert("RGB").save(PNG / dest_name)
        print(dest_name, out.size)


if __name__ == "__main__":
    main()
