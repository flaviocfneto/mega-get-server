import {Activity, AlertCircle, BarChart3, CheckCircle2, DownloadCloud, Gauge} from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type {AnalyticsData} from '../types';
import {formatBytes, formatSpeed} from '../lib/format';

const ACCENT = 'var(--ft-accent)';
const ACCENT_MID = 'color-mix(in_srgb, var(--ft-accent) 55%, white)';

type Props = {analytics: AnalyticsData | null};

export function AnalyticsView({analytics}: Props) {
  const daily = analytics?.daily_stats || [];
  const hasDaily = daily.some((d) => (d.bytes ?? 0) > 0 || (d.count ?? 0) > 0);

  return (
    <div className="mx-auto w-full max-w-6xl space-y-8">
      <h1 className="sr-only">Analytics</h1>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-3xl border border-[var(--ft-border)] bg-[var(--card)] p-6 shadow-sm">
          <div className="mb-4 flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-xl"
              style={{background: `color-mix(in_srgb, ${ACCENT} 12%, var(--ft-surface))`}}
            >
              <DownloadCloud className="h-5 w-5" style={{color: ACCENT}} aria-hidden />
            </div>
            <span className="text-xs font-bold uppercase tracking-wider text-[var(--muted-foreground)]">
              Total downloaded
            </span>
          </div>
          <div className="font-mono text-3xl font-bold tabular-nums text-[var(--foreground)]">
            {formatBytes(analytics?.total_downloaded_bytes || 0)}
          </div>
        </div>

        <div className="rounded-3xl border border-[var(--ft-border)] bg-[var(--card)] p-6 shadow-sm">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--ft-success-bg)]">
              <CheckCircle2 className="h-5 w-5 text-[var(--ft-success)]" aria-hidden />
            </div>
            <span className="text-xs font-bold uppercase tracking-wider text-[var(--muted-foreground)]">
              Completed
            </span>
          </div>
          <div className="font-mono text-3xl font-bold tabular-nums text-[var(--ft-success)]">
            {analytics?.total_transfers_completed || 0}
          </div>
        </div>

        <div className="rounded-3xl border border-[var(--ft-border)] bg-[var(--card)] p-6 shadow-sm">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--ft-danger-bg)]">
              <AlertCircle className="h-5 w-5 text-[var(--ft-danger)]" aria-hidden />
            </div>
            <span className="text-xs font-bold uppercase tracking-wider text-[var(--muted-foreground)]">
              Failed
            </span>
          </div>
          <div className="font-mono text-3xl font-bold tabular-nums text-[var(--ft-danger)]">
            {analytics?.total_transfers_failed || 0}
          </div>
        </div>

        <div className="rounded-3xl border border-[var(--ft-border)] bg-[var(--card)] p-6 shadow-sm">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--ft-warning-bg)]">
              <Gauge className="h-5 w-5 text-[var(--ft-warning)]" aria-hidden />
            </div>
            <span className="text-xs font-bold uppercase tracking-wider text-[var(--muted-foreground)]">
              Average speed
            </span>
          </div>
          <div className="font-mono text-3xl font-bold tabular-nums text-[var(--foreground)]">
            {formatSpeed(analytics?.average_speed_bps || 0)}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {hasDaily ? (
          <>
            <div className="rounded-3xl border border-[var(--ft-border)] bg-[var(--card)] p-6 shadow-sm">
              <h3 className="mb-6 flex items-center gap-2 text-sm font-bold text-[var(--foreground)]">
                <Activity className="h-4 w-4" style={{color: ACCENT}} aria-hidden />
                Download activity (last 7 days)
              </h3>
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={daily}>
                    <defs>
                      <linearGradient id="ftColorBytes" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={ACCENT_MID} stopOpacity={0.35} />
                        <stop offset="95%" stopColor={ACCENT_MID} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--ft-border)" vertical={false} />
                    <XAxis
                      dataKey="date"
                      stroke="var(--muted-foreground)"
                      fontSize={10}
                      tickFormatter={(val: string) => val.split('-').slice(1).join('/')}
                    />
                    <YAxis
                      stroke="var(--muted-foreground)"
                      fontSize={10}
                      tickFormatter={(val: number | string) => {
                        const n = typeof val === 'number' ? val : Number(val);
                        return formatBytes(Number.isFinite(n) ? n : 0).split(' ')[0] ?? '0';
                      }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'var(--card)',
                        borderColor: 'var(--ft-border)',
                        borderRadius: '12px',
                        fontSize: '12px',
                      }}
                      formatter={(value) => {
                        const n = typeof value === 'number' ? value : Number(value);
                        return [formatBytes(Number.isFinite(n) ? n : 0), 'Downloaded'];
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="bytes"
                      stroke={ACCENT}
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#ftColorBytes)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-3xl border border-[var(--ft-border)] bg-[var(--card)] p-6 shadow-sm">
              <h3 className="mb-6 flex items-center gap-2 text-sm font-bold text-[var(--foreground)]">
                <BarChart3 className="h-4 w-4 text-[var(--ft-success)]" aria-hidden />
                Transfers completed
              </h3>
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={daily}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--ft-border)" vertical={false} />
                    <XAxis
                      dataKey="date"
                      stroke="var(--muted-foreground)"
                      fontSize={10}
                      tickFormatter={(val: string) => val.split('-').slice(1).join('/')}
                    />
                    <YAxis stroke="var(--muted-foreground)" fontSize={10} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'var(--card)',
                        borderColor: 'var(--ft-border)',
                        borderRadius: '12px',
                        fontSize: '12px',
                      }}
                    />
                    <Bar dataKey="count" fill="var(--ft-success)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </>
        ) : (
          <div className="rounded-3xl border border-dashed border-[var(--ft-border)] bg-[var(--card)] p-8 text-center text-sm text-[var(--muted-foreground)] lg:col-span-2">
            Daily charts appear after completed transfers are recorded (last 7 days). Summary cards above still
            update from current activity.
          </div>
        )}
      </div>
    </div>
  );
}
