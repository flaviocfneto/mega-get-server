# FileTugger brand assets

Complete brand and design-token package for FileTugger — a self-hosted batch
downloader for MEGA, Google Drive, and direct links.

## Contents

### Logos and icons
- `ft-icon-app.svg` — master 512×512 colour glyph
- `ft-icon-mono.svg` — single-tone variant using `currentColor` (mask-based interlock)
- `ft-icon-animated.svg` — standalone animated SVG with hover and `.ft-downloading` states
- `ft-favicon.svg` — simplified glyph for 16–32 px display
- `ft-logo-wordmark.svg` — horizontal lockup with tagline
- `ft-logo-stacked.svg` — vertical lockup with tagline
- `ft-readme-banner.svg` — 1280×320 README banner

### React components
- `FtIcon.tsx` — static glyph, three variants (`color` / `mono` / `favicon`)
- `FtIconAnimated.tsx` — animated glyph with `downloading` prop

### Design tokens
- `ft-tokens.css` — CSS custom properties for the Fjord palette, light + dark modes
- `ft-tailwind.config.js` — Tailwind theme extension referencing the tokens

### PWA
- `manifest.webmanifest` — web app manifest snippet (drop into `public/`)

### Documentation
- `BRAND.md` — full brand specification for designers extending the system
- `README.md` — this file

## Quick start

### 1. Drop the tokens into your Vite app

```ts
// src/main.tsx
import "./styles/ft-tokens.css";
```

### 2. Wire up Tailwind

```js
// tailwind.config.js
import { ftTheme } from "./ft-tailwind.config.js";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: { extend: ftTheme },
};
```

### 3. Use the icon

```tsx
import { FtIcon } from "./components/FtIcon";
import { FtIconAnimated } from "./components/FtIconAnimated";

// Static
<FtIcon size={40} />

// Animated, reacting to download queue state
<FtIconAnimated size={40} downloading={queue.activeCount > 0} />
```

### 4. Wire up the favicon and PWA manifest

```html
<!-- index.html -->
<link rel="icon" type="image/svg+xml" href="/icons/ft-favicon.svg" />
<link rel="manifest" href="/manifest.webmanifest" />
<meta name="theme-color" content="#0F1713" />
```

### 5. Generate PNG icons for the manifest

The manifest references PNG fallbacks. Generate them from the master SVG:

```bash
npx sharp-cli -i ft-icon-app.svg -o ft-icon-192.png resize 192 192
npx sharp-cli -i ft-icon-app.svg -o ft-icon-512.png resize 512 512
# Maskable: pad the master with safe-zone background before rasterising
```

## Theme toggle

```tsx
const toggleTheme = () => {
  const html = document.documentElement;
  html.classList.toggle("dark");
  localStorage.setItem(
    "ft-theme",
    html.classList.contains("dark") ? "dark" : "light"
  );
};

useEffect(() => {
  if (localStorage.getItem("ft-theme") === "dark") {
    document.documentElement.classList.add("dark");
  }
}, []);
```

## Animated icon: behaviour

The animated icon has three states:

| State | Trigger | Behaviour |
|---|---|---|
| Idle | Default | Static |
| Hover | Mouse over | One-shot tug — chain links pull apart and snap back, paper tilts 1° |
| Downloading | `.ft-downloading` class or `downloading` prop | Continuous looped tug at ~1.4 s cadence |

All animations are disabled when the user has `prefers-reduced-motion: reduce`
set. The tug uses a slight overshoot easing curve for character.

## Brand specification

See `BRAND.md` for the complete designer handover document — palette, geometry,
construction rules, what can and cannot change, and guidance for extending the
system into new media.
