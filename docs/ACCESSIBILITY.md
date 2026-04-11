# Accessibility (FileTugger web)

This project targets **WCAG 2.2 Level AA** for the React app in `web/`. Authoritative product criteria live in [FRONTEND-DESIGN-PHILOSOPHY.md](FRONTEND-DESIGN-PHILOSOPHY.md) §9; cross-cutting guidance is in [commands/accessibility-and-design-guidelines-v4.1.md](../commands/accessibility-and-design-guidelines-v4.1.md).

## Regression checklist

Use [commands/accessibility-tester.md](../commands/accessibility-tester.md) as the review template. After UI changes, at minimum:

1. **Automated:** run an accessibility scanner (e.g. axe DevTools or Lighthouse) on primary views.
2. **Keyboard:** Tab through the shell, modals, and queue actions; ensure focus order is logical and focus is always visible.
3. **Screen reader:** Spot-check with VoiceOver (macOS) or NVDA (Windows) on Transfers, Settings, and Diagnostics.
4. **Contrast:** Verify text and interactive states in both light and dark themes (normal text **4.5:1** vs background; UI components **3:1** where applicable).

## Document language

The app shell uses `<html lang="en-GB">` in [web/index.html](../web/index.html) to match British English copy conventions in the accessibility guide.
