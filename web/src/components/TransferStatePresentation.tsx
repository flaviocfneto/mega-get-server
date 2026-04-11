import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Pause,
  RefreshCw,
} from 'lucide-react';
import type {ReactNode} from 'react';

export function transferStateBadgeClassName(state: string): string {
  const base =
    'flex items-center gap-1.5 rounded-full border font-bold uppercase tracking-wider';
  switch (state) {
    case 'ACTIVE':
      return `${base} border-[var(--ft-border-strong)] text-[var(--ft-brand-teal)] bg-[color-mix(in_srgb,var(--ft-brand-teal)_12%,var(--ft-surface))]`;
    case 'QUEUED':
      return `${base} border-[var(--ft-warning)]/35 text-[var(--ft-warning)] bg-[var(--ft-warning-bg)]`;
    case 'PAUSED':
      return `${base} border-[var(--ft-border-strong)] text-[var(--ft-text-muted)] bg-[var(--ft-surface-sunken)]`;
    case 'RETRYING':
      return `${base} border-[var(--ft-warning)]/35 text-[var(--ft-warning)] bg-[var(--ft-warning-bg)]`;
    case 'COMPLETED':
      return `${base} border-[var(--ft-success)]/35 text-[var(--ft-success)] bg-[var(--ft-success-bg)]`;
    case 'FAILED':
      return `${base} border-[var(--ft-danger)]/35 text-[var(--ft-danger)] bg-[var(--ft-danger-bg)]`;
    default:
      return `${base} border-[var(--ft-border)] text-[var(--ft-text-muted)] bg-[var(--ft-surface-sunken)]`;
  }
}

export function TransferStateIcon({state}: {state: string}): ReactNode {
  const cls = 'w-3 h-3 shrink-0';
  switch (state) {
    case 'ACTIVE':
      return <RefreshCw className={`${cls} animate-spin`} aria-hidden />;
    case 'QUEUED':
      return <Clock className={cls} aria-hidden />;
    case 'PAUSED':
      return <Pause className={cls} aria-hidden />;
    case 'RETRYING':
      return <RefreshCw className={cls} aria-hidden />;
    case 'COMPLETED':
      return <CheckCircle2 className={cls} aria-hidden />;
    case 'FAILED':
      return <AlertCircle className={cls} aria-hidden />;
    default:
      return null;
  }
}
