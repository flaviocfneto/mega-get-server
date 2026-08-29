## 2026-08-29 - Contextual Action Buttons in Queue Lists
**Learning:** Repetitive action buttons (e.g. "Start", "Remove") rendered inside list items present ambiguity for screen reader users if missing item-specific accessible names.
**Action:** Always provide `aria-label`s referencing the item context (e.g., `aria-label={`Start transfer for ${item.url}`}`) for list action controls.
