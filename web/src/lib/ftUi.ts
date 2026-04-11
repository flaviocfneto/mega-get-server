/** Shared Tailwind fragments mapped to FileTugger design tokens (Fjord + cranberry accent). */

export const ftFocusRing =
  'focus:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--ft-accent)_45%,transparent)]';

export const ftBtnPrimary =
  'rounded-xl font-semibold bg-[var(--ft-accent)] hover:bg-[var(--ft-accent-hover)] text-[var(--ft-accent-fg)] shadow-md transition-colors disabled:opacity-50 disabled:pointer-events-none';

export const ftBtnPrimarySm = `${ftBtnPrimary} px-4 py-2 text-xs font-bold`;

export const ftBtnPrimaryMd = `${ftBtnPrimary} px-6 py-2.5 text-sm font-bold`;

export const ftBtnPrimaryLg = `${ftBtnPrimary} px-8 py-3 text-sm font-semibold`;

export const ftBtnGhost = 'rounded-xl border border-[var(--ft-border)] bg-[var(--muted)] hover:bg-[var(--border)] text-[var(--foreground)] transition-colors';

export const ftTabActive = 'text-[var(--ft-accent)]';

export const ftTabInactive = 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]';

export const ftTabUnderline = 'h-0.5 rounded-full bg-[var(--ft-accent)]';

export const ftCard = 'rounded-2xl border border-[var(--ft-border)] bg-[var(--card)] shadow-sm';

export const ftInput =
  'w-full rounded-xl border border-[var(--ft-border)] bg-[var(--background)] px-4 py-3 text-sm text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] transition-shadow';

/** Muted field surface (settings modals, dense forms). */
export const ftInputMuted =
  'w-full rounded-xl border border-[var(--ft-border)] bg-[var(--muted)] px-4 py-2.5 text-sm text-[var(--foreground)] transition-shadow';
