## 2026-05-02 - Inline Confirmation Pattern

**Learning:** Destructive but frequent actions (like clearing logs or cancelling transfers) benefit from an inline "click-to-confirm" pattern rather than full-screen modals. This maintains user context and high task speed while providing a sufficient safety barrier.

**Action:** Use a local state `showConfirm` to toggle the button's interior into a confirmation UI: `[Label?] [Yes (primary-danger)] [X (ghost)]`. Ensure the container has `animate-in fade-in zoom-in` for smooth transition.
