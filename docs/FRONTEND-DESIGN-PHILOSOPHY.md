# FileTugger Frontend Design Philosophy (B2B Clarity)

This document is the implementation-ready design spec for upgrading the React frontend in `web/src/App.tsx`.

It is informed by:

- `commands/design-md` examples (high-clarity B2B reference patterns)
- `commands/ui-designer.md`
- `commands/ux-researcher.md`
- `commands/accessibility-and-design-guidelines-v4.1.md` (WCAG 2.2 AA baseline)
- `DESIGN/docs/BRAND.md`
- `DESIGN/tokens/ft-tokens.css`
- `DESIGN/tokens/ft-tailwind.config.js`

## 1) Product Design Philosophy

### 1.1 Operational clarity first

- Every screen must answer three questions within 3-5 seconds:
  - What is happening now?
  - What needs my attention?
  - What can I do next?
- Prefer information hierarchy and legibility over decorative complexity.
- Prioritize table/list scan speed, stable layouts, and explicit state labels.

### 1.2 Brand disciplined, not brand loud

- Use FileTugger identity intentionally:
  - Ink/neutral system for structure.
  - Cranberry for primary emphasis and actions.
  - Gold stays reserved for the brand mark, not general UI accents.
- Never redraw brand symbol geometry; use canonical assets.

### 1.3 Systemized interaction model

- Reuse one pattern language across tabs:
  - shell, filters, section headers, status chips, action bars, dialogs.
- Standardize all feedback into `info | success | warning | error`.
- Use predictable keyboard and focus behavior on all interactive controls.

### 1.4 Research-informed ergonomics

- Optimize for primary jobs:
  - add link, monitor queue, fix errors, tune settings, inspect diagnostics.
- Reduce cognitive load using progressive disclosure and grouped controls.
- Keep technical wording only where required (MEGA/MEGAcmd contexts).

## 2) Brand And Token Constraints (Non-Negotiable)

From `DESIGN/docs/BRAND.md` and token files:

- Locked colors:
  - `--ft-brand-gold: #F5B82E`
  - `--ft-brand-teal: #2DD4BF`
  - `--ft-brand-ink: #0F1713`
- Cranberry accent (`--ft-accent`) is the warm UI spark.
- Preserve canonical icon angles and interlock construction.
- Keep green-tinted neutral palette (avoid pure gray/black styling drift).
- Respect dark-mode token mappings and `.dark` override behavior.

## 3) Baseline Audit Of Current Frontend

Target file: `web/src/App.tsx` (single-file app shell and all tabs).

### 3.1 Structural observations

- All core surfaces are in one large component:
  - shell/navigation
  - transfers
  - history
  - analytics
  - settings modal
  - login modal
  - diagnostics panel
- Network orchestration and rendering logic are tightly coupled.

### 3.2 UX friction points

- Very high visual density in transfers/settings areas.
- Inconsistent visual semantics between state badges and action buttons.
- Multiple action clusters compete for attention without fixed priority.
- Diagnostics information is useful but not strongly action-oriented.

### 3.3 Consistency gaps

- Mixed ad-hoc classes and color intents in different sections.
- Filter/search/action bars vary in layout rhythm across tabs.
- Empty states differ in tone and affordance quality.

## 4) UX Map Across Full Surfaces

### 4.1 Primary user journeys

1. Submit download link
2. Monitor queue progress
3. Perform bulk queue actions
4. Inspect errors/logs/diagnostics
5. Configure settings and account context
6. Review history and analytics

### 4.2 Desired interaction model

- Global shell:
  - identity, primary tabs, global status at top.
- Per-tab:
  - summary row (KPIs),
  - filter/search row,
  - main content region,
  - contextual action bar.

## 5) UI Foundation Spec

## 5.1 Token usage matrix

- Backgrounds and surfaces:
  - `bg`: `--ft-bg`
  - cards/panels: `--ft-surface`
  - raised overlays: `--ft-surface-raised`
  - recessed blocks: `--ft-surface-sunken`
- Borders:
  - default: `--ft-border`
  - active/strong: `--ft-border-strong`
  - subtle separators: `--ft-border-subtle`
- Text:
  - primary: `--ft-text`
  - secondary labels: `--ft-text-muted`
  - helper/meta: `--ft-text-subtle`
- Emphasis and semantics:
  - primary action: `--ft-accent`
  - success/warning/danger/info token families from `ft-tokens.css`.

### 5.2 Layout primitives

- Shell max width: keep `max-w-7xl`.
- Section cadence: 24-32px vertical rhythm.
- Control density levels:
  - comfortable (default): forms/settings.
  - compact: transfer/history rows.
- Responsive behavior:
  - desktop first for operational use,
  - preserve keyboard access at all breakpoints.

### 5.3 Typography and font roles

FileTugger uses a four-family stack aligned with [commands/accessibility-and-design-guidelines-v4.1.md](../commands/accessibility-and-design-guidelines-v4.1.md) **Part 1 — Typography Strategy**: maximise legibility and reduce ambiguous glyphs in operational UIs, with clear separation between prose UI, technical strings, long-form reading, and display-level headings.

| Font | Core role | Where to use |
| --- | --- | --- |
| **Atkinson Hyperlegible Next** | Primary UI and body | Paragraphs, buttons, navigation, forms, tooltips, standard chrome. |
| **Atkinson Hyperlegible Mono** | Technical and tabular | Code snippets, paths, serial numbers, timestamps, dense data tables, diagnostics. |
| **Lora** | Secondary serif | Editorial or help content, quotes, future reading modes. |
| **Fraunces** | Display | Hero or marketing surfaces, **H1 / H2** only — not dense tables or small controls. |

**CSS tokens** (see `DESIGN/tokens/ft-tokens.css`):

- `--ft-font-sans` → Atkinson Hyperlegible Next (+ system UI fallbacks)
- `--ft-font-mono` → Atkinson Hyperlegible Mono (+ monospace fallbacks)
- `--ft-font-serif` → Lora (+ serif fallbacks)
- `--ft-font-display` → Fraunces (+ display fallbacks)

**Type scale (defaults):**

- Base UI: **16px minimum** for interactive labels and primary body (WCAG 2.2 AA for normal text under ~18pt at **4.5:1** contrast vs background).
- Compact rows (Transfers/History): secondary metadata may be smaller only if contrast and **24×24px** minimum hit areas still pass.
- Line height: **1.5** for body paragraphs; slightly tighter for single-line row metadata where needed.
- **Tabular numerals:** use mono family or `font-variant-numeric: tabular-nums` on KPIs and aligned counts.

**Loading:** the web app loads families via Google Fonts from `web/index.html` (see `web/src/main.tsx` + `web/src/index.css`). Self-hosting is allowed if file sizes and `font-display: swap` behaviour are preserved.

## 6) Component Standardization Blueprint

Apply consistently across all tabs.

### 6.1 Top shell and nav

- Fixed header with:
  - FileTugger identity block,
  - primary tab set,
  - account/session entry points.
- Active tab indicator pattern shared across all tabs.

### 6.2 Filter bars and search

- One canonical filter row:
  - search first,
  - categorical filters next,
  - secondary toggles last.
- Keep clear/reset actions right-aligned and explicit.

### 6.3 Lists and row cards

- Transfer rows:
  - state/priority first-class,
  - filename/path secondary,
  - controls grouped by risk and frequency.
- History rows:
  - compact metadata rhythm, predictable timestamp formatting.

### 6.4 Action bars

- Bulk actions grouped into:
  - non-destructive (pause/resume/tag),
  - destructive (cancel/remove) separated visually.
- Confirm destructive actions when selection count > 1.

### 6.5 Analytics widgets

- KPI row first (4-6 metrics max).
- Trend charts second with clear legends and empty states.
- No dense chart clutter; focus on queue health and throughput.

### 6.6 Settings and diagnostics

- Settings:
  - grouped by outcomes (Queue, Performance, Automation, Privacy).
  - inline help text for non-obvious options.
- Diagnostics:
  - convert passive data into actions:
    - status + impact + next step command.

### 6.7 Dialogs and overlays

- Shared modal template:
  - title, short intent copy, primary/secondary actions.
- Keyboard behavior:
  - `Esc` closes (except when blocked by critical validation),
  - initial focus defined,
  - focus trap preserved.

## 7) Per-Tab Redesign Decisions

### 7.1 Transfers

- Raise queue-state visibility:
  - active/queued/failed counts near top.
- Simplify row controls:
  - common actions always visible,
  - advanced options in compact overflow.
- Preserve speed:
  - keyboard-friendly selection and bulk operations.

### 7.2 History

- Improve retrieval:
  - consistent search + date/group affordances.
- Increase scanability:
  - concise metadata and clear recency cues.

### 7.3 Analytics

- Focus narrative:
  - queue health now,
  - historical trend second,
  - actionable anomalies highlighted.

### 7.4 Settings

- Reduce form fatigue:
  - section grouping, progressive disclosure.
- Add guardrails:
  - helper text for risky settings and side effects.

### 7.5 Diagnostics

- Reframe as troubleshooting center:
  - "Issue", "Why it matters", "Run this", "Expected result".

## 8) Copy And Micro-Interaction Rules

### 8.1 UX writing

- Use concise operational verbs: Add, Retry, Pause, Resume, Clear.
- Avoid vague labels; every action label should imply outcome.
- Keep MEGA/MEGAcmd naming only where technically required.

### 8.2 Motion

- Use short transitions (100-200ms) for state continuity.
- No decorative heavy animations in core queue operations.
- Respect reduced-motion preferences for non-critical motion.

## 9) Accessibility And Quality Criteria

Typography must satisfy the same WCAG 2.2 AA bar as colour and interaction: **1.4.3** contrast for text, **1.4.11** for non-text UI, **2.4.7** visible focus, **2.1.1** keyboard operation, **2.5.8** minimum target size where applicable. See `commands/accessibility-and-design-guidelines-v4.1.md` Tier 1 cheat sheet.

### 9.1 Tier 1 (non-negotiable) — product checklist

| Criterion | Intent |
| --- | --- |
| Keyboard | Every primary flow (add link, queue actions, settings, diagnostics) works without pointer. |
| Focus | `:focus-visible` uses `--ft-focus-ring` (or equivalent) on all interactive controls. |
| Contrast | Normal text **4.5:1**; large text **3:1**; UI components (borders, icons on controls) **3:1** vs adjacent colours. |
| Targets | Touch/click targets **at least 24×24px** effective (padding counts). |
| Name | Icon-only controls have accessible names (`aria-label` / `aria-labelledby`). |
| Colour | State is never conveyed by colour alone (pair with text, icon, or pattern). |
| Language | Document language set on `<html>` (see **en-GB** for British English UI copy). |
| Skip link | First focusable control is a **skip to main content** link for the SPA shell. |
| Structure | One **h1** per view; heading levels don’t skip; landmarks: `header`, `nav` (with `aria-label`), `main`. |

### 9.2 Tier 2 — when the feature exists

| Criterion | Intent |
| --- | --- |
| Live regions | Queue status, errors, and diagnostics updates that change without navigation use `aria-live` (usually `polite`) so assistive tech isn’t silent. |
| Modals | Focus trap, **Escape** closes, focus returns to trigger; initial focus on dialog title or first field. |
| Forms | Labels tied to inputs; errors describe what failed and how to fix. |
| Motion | Non-essential animation respects `prefers-reduced-motion`. |

### 9.3 Regression QA

After material UI changes, run through [commands/accessibility-tester.md](../commands/accessibility-tester.md): automated scan (e.g. axe), keyboard-only pass, spot-check with a screen reader, and contrast verification on light/dark. See also [docs/ACCESSIBILITY.md](ACCESSIBILITY.md).

### 9.4 Performance sanity

- Keep interaction latency low on transfer-heavy screens.
- Avoid expensive visual effects in high-frequency updates.
- Preserve responsive behavior on lower-end devices.

### 9.5 Consistency acceptance

- All tabs use shared shell/filter/action/list primitives.
- Semantic colors and state labels are uniform everywhere.
- Empty/loading/error states follow one template family.

## 10) Implementation Phasing Recommendation

1. Extract primitives from `web/src/App.tsx` without behavior changes.
2. Apply shell + filter + action bar standardization first.
3. Redesign tabs in order: Transfers -> Diagnostics -> Settings -> History -> Analytics.
4. Finish with copy/motion/accessibility pass and regression checks.

## 11) Success Metrics

- Reduced time-to-first-action on Transfers.
- Faster error recovery from Diagnostics workflows.
- Lower user confusion in settings edits.
- Fewer visual consistency defects across tabs.
- Accessibility checklist pass for all primary journeys.
