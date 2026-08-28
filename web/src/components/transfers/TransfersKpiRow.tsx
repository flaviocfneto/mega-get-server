import {memo, useMemo} from 'react';
import type {Transfer} from '../../types';

type Props = {transfers: Transfer[]};

// Wrap in React.memo to prevent unnecessary re-renders when parent state updates.
export const TransfersKpiRow = memo(function TransfersKpiRow({transfers}: Props) {
  // Compute transfer count metrics in a single O(N) loop instead of 4 separate array filter passes.
  const {active, queued, failed, completed} = useMemo(() => {
    let activeCount = 0;
    let queuedCount = 0;
    let failedCount = 0;
    let completedCount = 0;

    for (let i = 0; i < transfers.length; i++) {
      const state = transfers[i].state;
      if (state === 'ACTIVE') {
        activeCount++;
      } else if (state === 'QUEUED') {
        queuedCount++;
      } else if (state === 'FAILED' || state === 'RETRYING') {
        failedCount++;
      } else if (state === 'COMPLETED') {
        completedCount++;
      }
    }

    return {
      active: activeCount,
      queued: queuedCount,
      failed: failedCount,
      completed: completedCount,
    };
  }, [transfers]);

  const items = [
    {label: 'Active', value: active, desc: 'Downloading now', tone: 'teal' as const},
    {label: 'Queued', value: queued, desc: 'Waiting', tone: 'warn' as const},
    {label: 'Needs attention', value: failed, desc: 'Failed or retrying', tone: 'danger' as const},
    {label: 'Completed', value: completed, desc: 'Finished in list', tone: 'ok' as const},
  ];

  return (
    <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4" aria-label="Queue summary">
      {items.map((k) => (
        <div
          key={k.label}
          className="rounded-xl border border-[var(--ft-border)] bg-[var(--card)] px-4 py-3 shadow-sm"
        >
          <div className="text-[10px] font-bold uppercase tracking-wider text-[var(--muted-foreground)]">
            {k.label}
          </div>
          <div
            className={`mt-1 font-mono text-2xl font-bold tabular-nums ${
              k.tone === 'teal'
                ? 'text-[var(--ft-brand-teal)]'
                : k.tone === 'warn'
                  ? 'text-[var(--ft-warning)]'
                  : k.tone === 'danger'
                    ? 'text-[var(--ft-danger)]'
                    : 'text-[var(--ft-success)]'
            }`}
          >
            {k.value}
          </div>
          <div className="mt-0.5 text-[10px] text-[var(--muted-foreground)]">{k.desc}</div>
        </div>
      ))}
    </div>
  );
});
