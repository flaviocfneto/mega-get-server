# FileTugger — Brand Identity Specification

A handover document for designers extending the FileTugger visual system.

## 1. Concept

FileTugger is a desktop tool for batch-downloading files from MEGA, Google Drive, and direct links. The mark needs to communicate three things at once: **files** (what you're getting), **links** (how you specify them), and **pulling/fetching** (what the app does for you).

The logo solves this by layering two distinct symbols:

- A **document** (the file) — recognisable, friendly, slightly tilted to feel like it's been picked up rather than placed
- An **interlocked chain** (the link) — bold, diagonal, dominant, suggesting both "hyperlink" and "physical pull"

The chain dominates because the app's hero behaviour is the *tugging*. The document grounds the metaphor — without it, the mark would just be a generic chain symbol shared with dozens of fintech and security tools.

## 2. Construction

### 2.1 The document

A rounded rectangular page rendered on a 512×512 canvas. Three corners (top-right, bottom-right, bottom-left) use a 48px corner radius drawn with quadratic Bézier curves. The fourth corner — top-left — is a sharp diagonal cut representing a folded-over corner.

**Tilt:** the entire document is rotated **-13°** around the canvas centre (256, 256). This counter-angles the chain's -43° tilt and gives the composition rhythm.

### 2.2 The folded corner

A 76×76 right-angled triangle filled with the cranberry accent colour rather than a darker version of the paper. The fold reads as the *underside* of the page — and we use that surface as a window into the brand's accent colour, tying mark and UI together.

**Why top-left:** the chain's upper-right link endpoint sits in the upper-right region of the canvas. Placing the fold in the top-left puts it in the only quadrant the chain doesn't enter, eliminating visual collision.

### 2.3 The chain

Two interlocking links rendered as rounded rectangles (`rx="80"`) with no fill, only strokes.

- Both links are 420×160 with an 80px corner radius
- Stroke weight: **38px**
- Group rotation: **-43°**

### 2.4 The interlock illusion

Real chain links thread through each other — gold passes behind teal at one crossing point and in front at the other.

1. Draw the gold link in full
2. Draw the teal link in full on top of the gold
3. Redraw only the bottom half of the gold link on top of the teal

The result reads as a true weave. The mono variant achieves the same effect with SVG mask knockouts at the crossing points.

## 3. Colour palette — Fjord

### 3.1 Locked brand colours (never change)

| Token | Hex | Role |
|---|---|---|
| `--ft-brand-gold` | `#F5B82E` | Gold chain link |
| `--ft-brand-teal` | `#2DD4BF` | Teal chain link |
| `--ft-brand-ink` | `#0F1713` | Document outline, primary text — green-tinted near-black |

Gold and teal are roughly complementary. Both at high but not maximum saturation.

### 3.2 Document body

| Token | Hex | Role |
|---|---|---|
| Document fill | `#F4F5F3` | Fjord paper, identical to light-mode background |
| Document outline | `#0F1713` | Same as `--ft-brand-ink` |

The paper colour matches the app's light-mode background exactly. On a Fjord-themed app, the document body blends into the canvas while the chain pops off it.

### 3.3 Accent — cranberry

| Token | Hex (light) | Hex (dark) | Role |
|---|---|---|---|
| `--ft-accent` | `#BE123C` | `#FB7185` | Folded corner, buttons, focus rings, "Tugger" wordmark |

The only warm colour in the UI palette. Chain gold is reserved for the brand mark only.

### 3.4 Light mode neutrals

| Token | Hex |
|---|---|
| `--ft-bg` | `#F4F5F3` |
| `--ft-surface` | `#FFFFFF` |
| `--ft-surface-sunken` | `#EDEFEC` |
| `--ft-border` | `#DDE1DC` |
| `--ft-border-strong` | `#C4CBC4` |
| `--ft-text` | `#0F1713` |
| `--ft-text-muted` | `#5C6660` |
| `--ft-text-subtle` | `#94A099` |

All neutrals tinted slightly green to match the document paper. Not pure greys.

### 3.5 Dark mode neutrals

| Token | Hex |
|---|---|
| `--ft-bg` | `#0C1210` |
| `--ft-surface` | `#161D18` |
| `--ft-surface-raised` | `#1F2822` |
| `--ft-border` | `#283027` |
| `--ft-text` | `#F0F3F0` |
| `--ft-text-muted` | `#94A099` |

Deep forest-floor rather than neutral charcoal. Same green undertone as light mode.

### 3.6 Semantic colours

| Role | Light | Dark |
|---|---|---|
| Success | `#0F766E` | `#2DD4BF` (brand teal) |
| Warning | `#D97706` | `#F59E0B` |
| Danger | `#BE123C` (brand accent) | `#FB7185` |
| Info | `#475569` | `#94A099` |

Success in dark mode reuses brand teal; danger in both modes is the brand cranberry. Semantic and brand systems share colours.

## 4. Composition rules

### 4.1 Hierarchy

Visual weight, heaviest to lightest:

1. Chain (38px stroke, saturated colour, dominant diagonal)
2. Document outline + fold (7px stroke, ink colour, secondary tilt)
3. Document body fill (paper colour, recedes)

The chain must always read first. Below 24px, omit the document — the chain alone is the simplified glyph.

### 4.2 Angles

- Document tilt: **-13°**
- Chain tilt: **-43°**
- Angular delta: **30°**

The 30° gap is the source of compositional rhythm. Do not change either angle independently. Rotate the whole composition as a group if needed.

### 4.3 Margins

Chain endpoints stop ~30 units short of canvas corners. Document has at least 60 units of margin on its tilt-side. For tile backgrounds, `border-radius: 96px` on a 512×512 tile is safe.

## 5. Typography

### 5.1 Wordmark

| Element | Treatment |
|---|---|
| Typeface | **Fraunces** (display), weight 700–800 |
| "File" colour | `#0F1713` (ink) |
| "Tugger" colour | `#BE123C` (cranberry) |
| Set | Sentence case, joined as one word |

### 5.2 Tagline

| Element | Treatment |
|---|---|
| Text | `MEGA · GOOGLE DRIVE · DIRECT LINKS` |
| Typeface | **Atkinson Hyperlegible Next**, weight 600 |
| Colour | `#5C6660` |
| Letter spacing | +3.5 |
| Case | ALL CAPS |
| Separator | Middle-dot (·, U+00B7) |

### 5.3 Lockups

- **Horizontal:** glyph left, wordmark right with tagline beneath
- **Stacked:** glyph centred above wordmark and tagline

Both reference the canonical SVG glyph at 31% scale. Never redraw.

## 6. Variants

| Variant | Purpose | Construction |
|---|---|---|
| `color` | Default. Headers, app tile, marketing | Layered drawing — paper fill, cranberry fold, ink outline, gold/teal interlocked chain |
| `mono` | Single-tone, photo overlays, embossing, tinted contexts | Document outline at 50% opacity, chain with mask-based interlock, inherits `currentColor` |
| `favicon` | 16–32px display | Same as color but on 64×64 viewBox with proportional strokes |
| `animated` | Hover and active-download states | Color variant with CSS transform animations on chain groups and paper |

## 7. Designer freedoms and constraints

### Can change

- Tagline text
- Lockup spacing and alignment within rules
- Glyph size relative to text in lockups
- Background tile colour and corner radius for app icons
- Animation timing and easing
- New variants for new contexts (notification badges, avatar masks)
- Accent shade for special campaigns (limited use)

### Cannot change

- Brand colours (`#F5B82E`, `#2DD4BF`, `#0F1713`)
- The two angles (-13° document, -43° chain) — only rotate as a group
- Chain construction (two links, this overlap, layered weave)
- Document corner geometry (three rounded + one diagonal fold)
- Fold position (top-left only — collision-fix decision)
- Wordmark capitalisation or split colouring
- Chain dominating document in visual weight

## 8. Extending the system

If a designer needs to take this into new territory — illustrations, marketing graphics, motion design, packaging — the principles to carry forward:

- **Two visual systems coexisting**: chain (saturated, geometric, diagonal) and paper (neutral, organic, counter-tilted). Any new asset should respect this duality.
- **Cranberry as the warm spark**: never let the UI become entirely cool. There must always be a single warm element pulling the eye.
- **Green undertones throughout**: no pure greys, whites, or blacks. Even dark mode has a forest tint.
- **The 30° rhythm**: when laying out compositions, look for opportunities to set elements at deliberate non-parallel, non-perpendicular angles.

The canonical SVGs and the tokens file are the source of truth.
