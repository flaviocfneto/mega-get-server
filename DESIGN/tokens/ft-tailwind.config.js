/**
 * FileTugger Tailwind theme extension — Fjord palette
 * ----------------------------------------------------
 * Merge this into your tailwind.config.js. The colour tokens reference the
 * CSS variables defined in ft-tokens.css, so swapping modes (light/dark)
 * only needs to change one place.
 *
 * Usage in your tailwind.config.js:
 *
 *   import { ftTheme } from "./ft-tailwind.config.js";
 *
 *   export default {
 *     content: ["./index.html", "./src/**\/*.{js,ts,jsx,tsx}"],
 *     darkMode: "class",  // enables <html class="dark">
 *     theme: {
 *       extend: ftTheme,
 *     },
 *   };
 *
 * Then in JSX:
 *   <div className="bg-surface text-fg border-border rounded-lg p-4">
 *   <button className="bg-accent text-accent-fg hover:bg-accent-hover">
 */

export const ftTheme = {
  colors: {
    // Brand (fixed in both modes — locked equity)
    brand: {
      gold: "var(--ft-brand-gold)",
      teal: "var(--ft-brand-teal)",
      ink: "var(--ft-brand-ink)",
    },

    // Surfaces
    bg: "var(--ft-bg)",
    surface: "var(--ft-surface)",
    "surface-raised": "var(--ft-surface-raised)",
    "surface-sunken": "var(--ft-surface-sunken)",

    // Borders
    border: "var(--ft-border)",
    "border-strong": "var(--ft-border-strong)",
    "border-subtle": "var(--ft-border-subtle)",

    // Text
    fg: "var(--ft-text)",
    "fg-muted": "var(--ft-text-muted)",
    "fg-subtle": "var(--ft-text-subtle)",
    "fg-inverse": "var(--ft-text-inverse)",

    // Accent (cranberry)
    accent: {
      DEFAULT: "var(--ft-accent)",
      hover: "var(--ft-accent-hover)",
      active: "var(--ft-accent-active)",
      fg: "var(--ft-accent-fg)",
      bg: "var(--ft-accent-bg)",
      border: "var(--ft-accent-border)",
    },

    // Semantic
    success: {
      DEFAULT: "var(--ft-success)",
      bg: "var(--ft-success-bg)",
      fg: "var(--ft-success-fg)",
    },
    warning: {
      DEFAULT: "var(--ft-warning)",
      bg: "var(--ft-warning-bg)",
      fg: "var(--ft-warning-fg)",
    },
    danger: {
      DEFAULT: "var(--ft-danger)",
      bg: "var(--ft-danger-bg)",
      fg: "var(--ft-danger-fg)",
    },
    info: {
      DEFAULT: "var(--ft-info)",
      bg: "var(--ft-info-bg)",
      fg: "var(--ft-info-fg)",
    },

    // Keep Tailwind's utility colours for edge cases
    transparent: "transparent",
    current: "currentColor",
    white: "#FFFFFF",
    black: "#000000",
  },

  borderRadius: {
    none: "0",
    sm: "var(--ft-radius-sm)",
    DEFAULT: "var(--ft-radius-md)",
    md: "var(--ft-radius-md)",
    lg: "var(--ft-radius-lg)",
    xl: "var(--ft-radius-xl)",
    full: "var(--ft-radius-full)",
  },

  boxShadow: {
    sm: "var(--ft-shadow-sm)",
    DEFAULT: "var(--ft-shadow-md)",
    md: "var(--ft-shadow-md)",
    lg: "var(--ft-shadow-lg)",
    none: "none",
  },

  fontFamily: {
    sans: ["var(--ft-font-sans)"],
    mono: ["var(--ft-font-mono)"],
    serif: ["var(--ft-font-serif)"],
    display: ["var(--ft-font-display)"],
  },
};
