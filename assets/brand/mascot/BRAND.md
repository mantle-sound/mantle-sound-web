# MAN mascot brand pack

Line-art mascot: a field recordist with headphones, seated on a mountain peak with a handheld recorder. Master artwork lives at `assets/brand/mascot/man.png` (white strokes on transparent black via alpha, 2042×1393 px). This folder holds line-art export variants for print, social, and UI.

Public URLs (Lektor `assets/`): `/brand/mascot/…`

## Brand colours (site CSS)

| Token | Hex | Use |
|-------|-----|-----|
| Primary text / line (dark UI) | `#333333` | Body, black-line mascot |
| Muted | `#666666`, `#999999` | Secondary marks, watermarks |
| Accent | `#ff5400` | Links, hover, orange-line mascot |
| Light plate | `#ffffff` | Backgrounds |
| Dark plate | `#000000` | Backgrounds, scroll mascot |
| Header tint | `#d3ebf3` | Logo area (not required on mascot) |

## File guide

### Master

| File | Description |
|------|-------------|
| `mascot-master-black-bg.png` | Copy of site master (`assets/brand/mascot/man.png`) |

### Line art (transparent background)

| File | When to use |
|------|-------------|
| `png/mascot-line-white-transparent.png` | Dark backgrounds, video overlays |
| `png/mascot-line-black-transparent.png` | Light backgrounds, documents |
| `png/mascot-line-gray-333333-transparent.png` | Neutral UI, `#333` |
| `png/mascot-line-gray-666666-transparent.png` | Muted UI |
| `png/mascot-line-gray-999999-transparent.png` | Disabled / watermark tone |
| `png/mascot-line-orange-transparent.png` | Accent campaigns, CTAs |
| `png/mascot-line-*-transparent-mirror.png` | Horizontal flip (matches scroll mascot) |

Sizes (black and white line only): `-64`, `-128`, `-256`, `-512` suffix.

### Line boldening (small line-art only)

For favicons and small sizes where thin lines disappear:

| File | Description |
|------|-------------|
| `png/mascot-silhouette-white-bold-transparent.png` | Thickened white lines |
| `png/mascot-silhouette-black-bold-transparent.png` | Thickened black lines |

### Full plates (opaque background)

| File | Description |
|------|-------------|
| `png/mascot-plate-black-bg-white-line.png` | Default “brand card” |
| `png/mascot-plate-white-bg-black-line.png` | Inverted card |
| `png/mascot-plate-black-bg-gray-line.png` | Subdued / draft watermark on black |

### Social & avatar

| File | Size | Description |
|------|------|-------------|
| `png/mascot-social-black-1200.png` | 1200×1200 | Open Graph / share image |
| `png/mascot-social-white-1200.png` | 1200×1200 | Light share card |
| `png/mascot-avatar-black-512.png` | 512×512 | Profile / app icon base |
| `png/mascot-avatar-white-512.png` | 512×512 | Light avatar base |

Square social and avatar PNGs use **contain** fit: crop to ink bounds, scale the **whole** mountain+figure into the square with margin (no zoom crop). Regenerate with `python3 assets/brand/mascot/scripts/generate-social-avatars.py`.

### Watermarks

| File | Opacity | Use |
|------|---------|-----|
| `png/mascot-watermark-white-22.png` | ~22% | Footer on dark imagery |
| `png/mascot-watermark-black-18.png` | ~18% | Footer on light pages |

## Site usage today

- Scroll mascot: `/brand/mascot/man.png` with `filter: invert(1)`, `transform: scaleX(-1)`, height 100px (`assets/static/style.css`, `.header-mascot`).
- Homepage logo image databag may reference `/brand/mascot/man.png`.

To switch the scroll mascot to a pack asset (e.g. pre-inverted white on transparent):

```html
<img class="header-mascot" src="/brand/mascot/png/mascot-line-white-transparent-mirror.png" alt="" aria-hidden="true">
```

Then remove `filter: invert(1)` from `.header-mascot` in CSS.

## Do

- Keep the figure recognizable: headphones, peak, seated pose.
- Use transparent PNGs on coloured backgrounds; use plates when you need a fixed black or white field.
- Prefer `-512` or bold line art below ~80 px display height.
- Mirror (`-mirror`) when the figure should face the same way as the scroll mascot.

## Don’t

- Stretch non-uniformly; always scale width and height together.
- Place orange-line variant on `#ff5400` backgrounds (no contrast).
- Imply the mascot alone is a certification or quality mark; it is identity, not accreditation.
- Recolour lines outside the palette without a specific campaign reason.

## Regenerating exports

From repo root, with ImageMagick 7 (`magick`):

```sh
SRC=assets/brand/mascot/man.png
OUT=assets/brand/mascot
# Re-run the export script in the commit that introduced this pack, or:
magick "$SRC" -alpha on -fuzz 8% -transparent black "$OUT/png/mascot-line-white-transparent.png"
magick "$SRC" -negate -alpha on -fuzz 8% -transparent white "$OUT/png/mascot-line-black-transparent.png"
```

After editing `assets/brand/mascot/man.png`, regenerate all variants and update checksums if any are committed in manifests.

## Preview

Open `preview.html` in a browser via the local site (e.g. `http://localhost:5000/brand/mascot/preview.html`) to compare variants side by side.
