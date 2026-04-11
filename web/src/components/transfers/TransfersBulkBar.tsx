import {AnimatePresence, motion, useReducedMotion} from 'motion/react';
import {Pause, Play, RefreshCw, X} from 'lucide-react';
import {ftFocusRing} from '../../lib/ftUi';

type Props = {
  count: number;
  onPause: () => void;
  onResume: () => void;
  onCancel: () => void;
  onRedownload: () => void;
  onSetPriority: (p: string) => void;
  onDeselectAll: () => void;
};

export function TransfersBulkBar({
  count,
  onPause,
  onResume,
  onCancel,
  onRedownload,
  onSetPriority,
  onDeselectAll,
}: Props) {
  const reduceMotion = useReducedMotion();

  return (
    <AnimatePresence>
      {count > 0 && (
        <motion.div
          initial={reduceMotion ? false : {height: 0, opacity: 0}}
          animate={reduceMotion ? false : {height: 'auto', opacity: 1}}
          exit={reduceMotion ? undefined : {height: 0, opacity: 0}}
          className="overflow-hidden"
        >
          <div className="flex flex-col gap-3 rounded-xl border border-[color-mix(in_srgb,var(--ft-accent)_35%,var(--ft-border))] bg-[color-mix(in_srgb,var(--ft-accent)_8%,var(--card))] p-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-wrap items-center gap-3">
              <span className="rounded-lg bg-[color-mix(in_srgb,var(--ft-accent)_15%,transparent)] px-2 py-1 text-xs font-bold text-[var(--ft-accent)]">
                {count} selected
              </span>
              <div className="mx-1 hidden h-4 w-px bg-[var(--ft-border)] sm:block" aria-hidden />
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={onPause}
                  className={`rounded-lg p-2 text-[var(--ft-accent)] hover:bg-[color-mix(in_srgb,var(--ft-accent)_15%,transparent)] ${ftFocusRing}`}
                  title="Pause selected"
                >
                  <Pause className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={onResume}
                  className={`rounded-lg p-2 text-[var(--ft-accent)] hover:bg-[color-mix(in_srgb,var(--ft-accent)_15%,transparent)] ${ftFocusRing}`}
                  title="Resume selected"
                >
                  <Play className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={onCancel}
                  className={`rounded-lg p-2 text-[var(--ft-danger)] hover:bg-[var(--ft-danger-bg)] ${ftFocusRing}`}
                  title="Cancel selected"
                >
                  <X className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={onRedownload}
                  className={`rounded-lg p-2 text-[var(--ft-accent)] hover:bg-[color-mix(in_srgb,var(--ft-accent)_15%,transparent)] ${ftFocusRing}`}
                  title="Redownload selected"
                >
                  <RefreshCw className="h-4 w-4" />
                </button>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase text-[var(--muted-foreground)]">Priority</span>
                <div className="flex rounded-lg border border-[var(--ft-border)] bg-[var(--muted)] p-0.5">
                  {(['LOW', 'NORMAL', 'HIGH'] as const).map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => onSetPriority(p)}
                      className={`rounded-md px-2 py-1 text-[9px] font-bold hover:bg-[var(--border)] ${ftFocusRing}`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
              <button
                type="button"
                onClick={onDeselectAll}
                className={`text-[10px] font-bold uppercase text-[var(--muted-foreground)] hover:text-[var(--foreground)] ${ftFocusRing} rounded px-2`}
              >
                Deselect all
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
