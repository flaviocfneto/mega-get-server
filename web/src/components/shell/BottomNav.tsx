import type {AppSectionId} from '../../navigation/primaryNav';
import {PRIMARY_NAV} from '../../navigation/primaryNav';
import {ftFocusRing} from '../../lib/ftUi';

type Props = {
  activeId: AppSectionId;
  onSelect: (id: AppSectionId) => void;
};

/** Mobile / tablet (<lg): fixed bottom primary nav. Desktop uses SidebarNav. */
export function BottomNav({activeId, onSelect}: Props) {
  return (
    <nav
      aria-label="Primary"
      className="fixed bottom-0 left-0 right-0 z-50 flex border-t border-[var(--ft-border)] bg-[var(--card)]/95 backdrop-blur-md lg:hidden"
      style={{paddingBottom: 'max(0.5rem, env(safe-area-inset-bottom))'}}
    >
      <div className="mx-auto flex h-14 w-full max-w-2xl items-stretch justify-around px-1">
        {PRIMARY_NAV.map(({id, label, shortLabel, icon: Icon}) => {
          const active = activeId === id;
          const navText = shortLabel ?? label;
          return (
            <button
              key={id}
              type="button"
              onClick={() => onSelect(id)}
              aria-current={active ? 'page' : undefined}
              className={`flex min-h-[44px] min-w-0 flex-1 flex-col items-center justify-center gap-0.5 rounded-lg px-0.5 text-[9px] font-bold transition-colors sm:text-[10px] ${ftFocusRing} ${
                active
                  ? 'text-[var(--ft-accent)]'
                  : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
              }`}
            >
              <Icon className={`h-5 w-5 shrink-0 ${active ? 'opacity-100' : 'opacity-80'}`} aria-hidden />
              <span className="max-w-full truncate leading-none">{navText}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
