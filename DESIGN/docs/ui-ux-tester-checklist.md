# UI/UX tester — improvement checklist (FileTugger)

Use this for structured UI and UX validation of `web/src` against product docs (`docs/UI-DESIGN.md`, `docs/FRONTEND-DESIGN-PHILOSOPHY.md`) and brand tokens (`BRAND.md`). Aligns with `ui-ux-tester.md`.

## Documentation and coverage

- [ ] Primary navigation and views mapped (`primaryNav`, Transfers, History, Analytics, System console).
- [ ] Each documented user-facing flow has a manual or automated path (e2e or checklist).

## Layout and spacing

- [ ] Spacing and padding feel consistent (filters, cards, bulk bars, panels); no accidental excessive or cramped whitespace.
- [ ] Alignment and grid behaviour checked at common viewport widths.

## Visual and brand

- [ ] Colours use Fjord/design tokens where applicable (`ft-tokens`, Tailwind theme); gold/teal reserved per brand for mark vs UI rules.
- [ ] Typography hierarchy readable; muted vs primary text distinction clear.
- [ ] Icons use canonical assets/components (`DESIGN/react/` or integrated copies) without ad hoc duplicates.

## Interaction and feedback

- [ ] Buttons and links show hover/focus/disabled states; focus visible for keyboard users.
- [ ] Loading states do not leave the user guessing (skeletons, spinners, or progress where appropriate).
- [ ] Empty states explain what to do next.

## Errors and recovery

- [ ] Errors from the API surface as understandable messages; destructive actions confirm when needed.
- [ ] Failed downloads or tool errors have a clear recovery path (retry, dismiss, or docs link).

## Motion and accessibility

- [ ] `prefers-reduced-motion` respected for animated brand assets (`FtIconAnimated` behaviour per brand README).
- [ ] Core tasks achievable without mouse where reasonable (tab order, landmarks).

## Logic and edge cases

- [ ] “Messy” inputs tested: rapid clicks, double submit, empty paste, very long labels.
- [ ] URL/deep-link behaviour matches expectations if the app supports section routing.

## Reporting

- [ ] Defects logged with severity, repro steps, and suggested fix; screenshots for visual issues.
