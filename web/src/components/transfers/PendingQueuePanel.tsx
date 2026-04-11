import {ListOrdered, Play, Trash2} from 'lucide-react';
import type {PendingQueueItem} from '../../types';
import {ftBtnGhost, ftBtnPrimarySm, ftFocusRing} from '../../lib/ftUi';

const HEADING_ID = 'history-queue-heading';

type Props = {
  items: PendingQueueItem[];
  busy: boolean;
  onRemove: (id: string) => void;
  onStart: (id: string) => void;
  onStartNext: () => void;
  onStartAll: () => void;
  /** Visible title for the panel (default matches History screen naming). */
  title?: string;
  /** Use h1 when this panel is the primary title for the view (e.g. History). */
  headingLevel?: 'h1' | 'h2';
};

export function PendingQueuePanel({
  items,
  busy,
  onRemove,
  onStart,
  onStartNext,
  onStartAll,
  title = 'History and Queue Management',
  headingLevel = 'h2',
}: Props) {
  const pending = items.filter((i) => i.status === 'PENDING');
  const failed = items.filter((i) => i.status === 'FAILED');

  const HeadingTag = headingLevel;
  const headingClass = 'text-base font-semibold text-[var(--foreground)]';

  return (
    <section className="rounded-2xl border border-[var(--ft-border)] bg-[var(--card)] p-4 shadow-md" aria-labelledby={HEADING_ID}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <HeadingTag id={HEADING_ID} className={headingClass}>
            {title}
          </HeadingTag>
          <p className="mt-1 max-w-2xl text-xs text-[var(--muted-foreground)]">
            Links here are stored in this app and are not sent to MEGAcmd until you start them. Rows with state “Queued” on the{' '}
            <span className="font-semibold text-[var(--foreground)]">Transfers</span> tab are already inside MEGAcmd&apos;s own queue.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy || pending.length === 0}
            onClick={() => onStartNext()}
            className={`inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-bold ${ftBtnGhost} ${ftFocusRing} disabled:opacity-50`}
          >
            <Play className="h-3.5 w-3.5" aria-hidden />
            Start next
          </button>
          <button
            type="button"
            disabled={busy || pending.length === 0}
            onClick={() => onStartAll()}
            className={`inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-bold ${ftBtnGhost} ${ftFocusRing} disabled:opacity-50`}
          >
            <ListOrdered className="h-3.5 w-3.5" aria-hidden />
            Start batch
          </button>
        </div>
      </div>

      {items.length === 0 ? (
        <p className="mt-4 text-sm text-[var(--muted-foreground)]">
          No saved links. Go to Transfers and use Add to queue to stash a MEGA URL without starting.
        </p>
      ) : (
        <ul className="mt-4 divide-y divide-[var(--ft-border-subtle)] rounded-xl border border-[var(--ft-border-subtle)]">
          {items.map((item) => (
            <li key={item.id} className="flex flex-col gap-2 p-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0 flex-1">
                <div className="truncate font-mono text-xs text-[var(--foreground)]" title={item.url}>
                  {item.url}
                </div>
                <div className="mt-1 flex flex-wrap gap-2 text-[10px] uppercase tracking-wide text-[var(--muted-foreground)]">
                  <span>{item.status}</span>
                  <span>{item.priority}</span>
                  {item.tags.length > 0 && <span>Tags: {item.tags.join(', ')}</span>}
                </div>
                {item.last_error && (
                  <p className="mt-1 text-xs text-[var(--ft-danger)]" role="status">
                    {item.last_error}
                  </p>
                )}
              </div>
              <div className="flex shrink-0 gap-2">
                {(item.status === 'PENDING' || item.status === 'FAILED') && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => onStart(item.id)}
                    className={`inline-flex items-center gap-1 rounded-lg px-2 py-1.5 text-xs font-bold ${ftBtnPrimarySm} ${ftFocusRing} disabled:opacity-50`}
                  >
                    <Play className="h-3 w-3" aria-hidden />
                    Start
                  </button>
                )}
                {item.status !== 'DISPATCHING' && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => onRemove(item.id)}
                    className={`inline-flex items-center gap-1 rounded-lg border border-[var(--ft-border)] px-2 py-1.5 text-xs font-bold text-[var(--muted-foreground)] hover:bg-[var(--muted)] ${ftFocusRing} disabled:opacity-50`}
                  >
                    <Trash2 className="h-3 w-3" aria-hidden />
                    Remove
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
