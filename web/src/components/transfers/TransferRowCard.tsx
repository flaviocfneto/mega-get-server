import {motion} from 'motion/react';
import {
  AlertCircle,
  CheckSquare,
  Clock,
  Copy,
  Gauge,
  Pause,
  Play,
  RefreshCw,
  RotateCcw,
  Square,
  X,
} from 'lucide-react';
import type {AppConfig, Transfer} from '../../types';
import {formatBytes, formatETA, formatSpeed} from '../../lib/format';
import {copyToClipboard} from '../../lib/clipboard';
import {ftFocusRing} from '../../lib/ftUi';
import {transferStateBadgeClassName, TransferStateIcon} from '../TransferStatePresentation';

type Props = {
  transfer: Transfer;
  config: AppConfig | null;
  selected: boolean;
  onToggleSelect: () => void;
  onAction: (action: 'pause' | 'resume' | 'cancel' | 'retry') => void;
  onSetSpeedLimit: (limitKbps: number) => void;
  reduceMotion: boolean;
};

export function TransferRowCard({
  transfer: t,
  config,
  selected,
  onToggleSelect,
  onAction,
  onSetSpeedLimit,
  reduceMotion,
}: Props) {
  const compact = !!config?.is_compact_mode;
  const privacy = !!config?.is_privacy_mode;

  return (
    <motion.div
      layout={!reduceMotion}
      initial={reduceMotion ? false : {opacity: 0, y: 20}}
      animate={reduceMotion ? false : {opacity: 1, y: 0}}
      exit={reduceMotion ? undefined : {opacity: 0, scale: 0.95}}
      className={`flex gap-4 rounded-2xl border bg-[var(--card)] shadow-sm transition-all group ${
        compact ? 'gap-3 p-3' : 'gap-4 p-5'
      } ${
        selected
          ? 'border-[var(--ft-accent)] ring-1 ring-[color-mix(in_srgb,var(--ft-accent)_28%,transparent)]'
          : 'border-[var(--ft-border)] hover:border-[color-mix(in_srgb,var(--ft-accent)_35%,var(--ft-border))]'
      }`}
    >
      <div className={compact ? 'pt-0.5' : 'pt-1'}>
        <button
          type="button"
          onClick={onToggleSelect}
          className={`rounded p-1 text-[var(--muted-foreground)] hover:bg-[var(--muted)] ${ftFocusRing}`}
          aria-pressed={selected}
          aria-label={selected ? 'Deselect transfer' : 'Select transfer'}
        >
          {selected ? (
            <CheckSquare className="h-5 w-5 text-[var(--ft-accent)]" aria-hidden />
          ) : (
            <Square className="h-5 w-5" aria-hidden />
          )}
        </button>
      </div>
      <div className="min-w-0 flex-1">
        <div className={`flex items-start justify-between gap-4 ${compact ? 'mb-2' : 'mb-4'}`}>
          <div className="min-w-0 flex-1">
            <div className="group/title flex items-center gap-2">
              <h3
                className={`mb-1 truncate font-medium text-[var(--foreground)] ${compact ? 'text-xs' : 'text-sm'} ${privacy ? 'blur-md select-none' : ''}`}
                title={t.filename}
              >
                {t.filename}
              </h3>
              <button
                type="button"
                onClick={() => void copyToClipboard(t.filename)}
                className="rounded p-1 opacity-0 transition-opacity group-hover/title:opacity-100 hover:bg-[var(--muted)]"
                title="Copy filename"
              >
                <Copy className="h-3 w-3 text-[var(--muted-foreground)]" />
              </button>
            </div>
            <div
              className={`flex flex-wrap items-center gap-3 text-[var(--muted-foreground)] ${compact ? 'text-[9px]' : 'text-[11px]'}`}
            >
              <span className="rounded border border-[var(--ft-border)] bg-[var(--muted)] px-1.5 py-0.5 font-mono">
                #{t.tag}
              </span>
              <span className={`max-w-[200px] truncate ${privacy ? 'blur-sm select-none' : ''}`}>{t.path}</span>
              {t.driver === 'http' && (
                <span
                  className="rounded border border-[var(--ft-border)] bg-[var(--muted)] px-1.5 py-0.5 text-[8px] font-bold uppercase text-[var(--muted-foreground)]"
                  title="Direct HTTP(S) download on server"
                >
                  HTTP
                </span>
              )}
              {t.priority && t.priority !== 'NORMAL' && (
                <span
                  className={`rounded border px-1.5 py-0.5 text-[8px] font-bold uppercase ${
                    t.priority === 'HIGH'
                      ? 'border-[var(--ft-danger)]/30 bg-[var(--ft-danger-bg)] text-[var(--ft-danger)]'
                      : 'border-[var(--ft-warning)]/30 bg-[var(--ft-warning-bg)] text-[var(--ft-warning)]'
                  }`}
                >
                  {t.priority}
                </span>
              )}
              {t.tags && t.tags.length > 0 && (
                <div className="flex flex-wrap items-center gap-1">
                  {t.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded border border-[color-mix(in_srgb,var(--ft-accent)_35%,var(--ft-border))] bg-[color-mix(in_srgb,var(--ft-accent)_10%,var(--ft-surface))] px-1.5 py-0.5 text-[8px] font-bold uppercase text-[var(--ft-accent)]"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div
            className={`${transferStateBadgeClassName(t.state)} ${compact ? 'px-2 py-0.5 text-[8px]' : 'px-2.5 py-1 text-[10px]'}`}
          >
            <TransferStateIcon state={t.state} />
            <span>{t.state}</span>
          </div>
        </div>

        <div className="space-y-3">
          <div className="mb-1 flex items-center justify-between text-xs">
            <div className="flex flex-col gap-1">
              <div className="flex flex-wrap items-center gap-2">
                {t.size_bytes === 0 ? (
                  <>
                    <span className="font-semibold text-[var(--foreground)]">{t.progress_pct}%</span>
                    <span className="text-[var(--muted-foreground)]">Unknown size</span>
                  </>
                ) : (
                  <>
                    <span className="font-semibold text-[var(--foreground)]">{formatBytes(t.downloaded_bytes)}</span>
                    <span className="text-[var(--muted-foreground)]">of {formatBytes(t.size_bytes)}</span>
                    <span className="ml-1 font-bold text-[var(--ft-accent)]">({t.progress_pct}%)</span>
                  </>
                )}
              </div>
              {t.state === 'ACTIVE' && t.speed_bps > 0 && (
                <div className="flex flex-wrap items-center gap-3 text-[10px] font-medium text-[var(--muted-foreground)]">
                  <span className="flex items-center gap-1">
                    <RefreshCw className="h-2.5 w-2.5" aria-hidden />
                    {formatSpeed(t.speed_bps)}
                  </span>
                  {t.size_bytes > 0 && (
                    <span className="flex items-center gap-1">
                      <Clock className="h-2.5 w-2.5" aria-hidden />
                      ETA: {formatETA((t.size_bytes - t.downloaded_bytes) / t.speed_bps)}
                    </span>
                  )}
                  <div className="group/limit ml-2 flex items-center gap-1 rounded border border-[var(--ft-border)] bg-[var(--muted)] px-1.5 py-0.5">
                    <Gauge className="h-2.5 w-2.5 text-[var(--ft-accent)]" aria-hidden />
                    <input
                      type="number"
                      defaultValue={t.speed_limit_kbps || 0}
                      onBlur={(e) => onSetSpeedLimit(parseInt(e.target.value, 10) || 0)}
                      className="w-12 bg-transparent text-[9px] font-bold focus:outline-none"
                      title="Speed limit (KB/s)"
                      aria-label="Speed limit kilobytes per second"
                    />
                    <span className="text-[8px] uppercase opacity-40">KB/s</span>
                  </div>
                </div>
              )}
            </div>
            <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
              {(t.state === 'FAILED' || t.state === 'RETRYING') && (
                <button
                  type="button"
                  onClick={() => onAction('retry')}
                  className={`rounded-lg p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[var(--foreground)] ${ftFocusRing}`}
                  title="Retry"
                >
                  <RotateCcw className="h-4 w-4" />
                </button>
              )}
              {t.state === 'PAUSED' ? (
                <button
                  type="button"
                  onClick={() => onAction('resume')}
                  className={`rounded-lg p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[var(--foreground)] ${ftFocusRing}`}
                  title="Resume"
                >
                  <Play className="h-4 w-4 fill-current" />
                </button>
              ) : t.state !== 'FAILED' && t.state !== 'RETRYING' ? (
                <button
                  type="button"
                  onClick={() => onAction('pause')}
                  className={`rounded-lg p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[var(--foreground)] ${ftFocusRing}`}
                  title="Pause"
                >
                  <Pause className="h-4 w-4 fill-current" />
                </button>
              ) : null}
              <button
                type="button"
                onClick={() => onAction('cancel')}
                className={`rounded-lg p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--ft-danger-bg)] hover:text-[var(--ft-danger)] ${ftFocusRing}`}
                title="Cancel"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
          <div className="relative h-2 overflow-hidden rounded-full bg-[var(--muted)]">
            <motion.div
              className={`relative h-full rounded-full ${t.state === 'FAILED' ? 'bg-[var(--ft-danger)]' : 'bg-[var(--ft-accent)]'}`}
              initial={{width: 0}}
              animate={{width: `${t.progress_pct}%`}}
              transition={reduceMotion ? {duration: 0} : {duration: 0.5, ease: 'easeOut'}}
            >
              {t.state === 'ACTIVE' && !reduceMotion && (
                <motion.div
                  className="absolute inset-0 bg-white/20"
                  animate={{x: ['-100%', '100%']}}
                  transition={{repeat: Infinity, duration: 1.5, ease: 'linear'}}
                />
              )}
            </motion.div>
          </div>
        </div>

        {t.state === 'RETRYING' && t.progress_pct === 0 && (
          <div className="mt-4 flex items-start gap-3 rounded-xl border border-[var(--ft-warning)]/30 bg-[var(--ft-warning-bg)] p-3">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--ft-warning)]" aria-hidden />
            <p className="text-[11px] leading-relaxed text-[var(--foreground)]">
              Stuck at 0%? Try{' '}
              <button
                type="button"
                onClick={() => onAction('resume')}
                className="font-bold text-[var(--ft-warning)] underline hover:no-underline"
              >
                resume
              </button>{' '}
              or{' '}
              <button
                type="button"
                onClick={() => onAction('cancel')}
                className="font-bold text-[var(--ft-warning)] underline hover:no-underline"
              >
                cancel
              </button>
              .
            </p>
          </div>
        )}
      </div>
    </motion.div>
  );
}
