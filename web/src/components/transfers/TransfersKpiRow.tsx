import type {Transfer} from '../../types';

type Props = {transfers: Transfer[]};

export function TransfersKpiRow({transfers}: Props) {
  const active = transfers.filter((t) => t.state === 'ACTIVE').length;
  const queued = transfers.filter((t) => t.state === 'QUEUED').length;
  const failed = transfers.filter((t) => t.state === 'FAILED' || t.state === 'RETRYING').length;
  const completed = transfers.filter((t) => t.state === 'COMPLETED').length;

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
}
