import type {AppSectionId} from '../../navigation/primaryNav';
import {PRIMARY_NAV} from '../../navigation/primaryNav';
import {ftFocusRing} from '../../lib/ftUi';

type Props = {
  activeId: AppSectionId;
  onSelect: (id: AppSectionId) => void;
};

/**
 * Desktop (lg+): vertical primary nav. Hidden below lg (see BottomNav).
 */
export function SidebarNav({activeId, onSelect}: Props) {
  return (
    <aside className="hidden lg:flex lg:w-60 lg:shrink-0 lg:flex-col lg:border-r lg:border-[var(--ft-border)] lg:bg-[var(--card)]/60">
      <nav aria-label="Primary" className="sticky top-16 flex max-h-[calc(100vh-4rem)] flex-col gap-1 self-start overflow-y-auto px-3 py-4">
        {PRIMARY_NAV.map(({id, label, icon: Icon}) => {
          const active = activeId === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => onSelect(id)}
              aria-current={active ? 'page' : undefined}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-bold transition-colors ${ftFocusRing} ${
                active
                  ? 'bg-[color-mix(in_srgb,var(--ft-accent)_18%,transparent)] text-[var(--ft-accent)]'
                  : 'text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[var(--foreground)]'
              }`}
            >
              <Icon className="h-5 w-5 shrink-0 opacity-90" aria-hidden />
              {label}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
