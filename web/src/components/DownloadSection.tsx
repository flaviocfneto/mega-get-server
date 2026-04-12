import {Plus, RefreshCw, Tag, X} from 'lucide-react';
import type {FormEvent} from 'react';
import type {TransferPriority} from '../types';
import {ftBtnGhost, ftBtnPrimaryLg, ftFocusRing, ftInput} from '../lib/ftUi';

type LastStatus = {
  phase: 'submitted' | 'active' | 'failed';
  message: string;
  url: string;
  updatedAt: number;
} | null;

type Telemetry = {
  clicks: number;
  lastFiredAt: number | null;
  lastOutcome: 'idle' | 'submitted' | 'failed' | 'blocked_no_url';
  lastUrlLength: number;
  lastHttpStatus: number | null;
  lastErrorMessage: string | null;
  lastWasOverride: boolean;
};

type Props = {
  url: string;
  onUrlChange: (v: string) => void;
  searchQuery: string;
  onSearchQueryChange: (v: string) => void;
  newDownloadTags: string;
  onNewDownloadTagsChange: (v: string) => void;
  newDownloadPriority: TransferPriority;
  onNewDownloadPriorityChange: (v: TransferPriority) => void;
  onSubmit: (e: FormEvent) => void;
  onAddToQueue: () => void;
  isDownloadSubmitting: boolean;
  lastDownloadStatus: LastStatus;
  onRetryLast: () => void;
  downloadTelemetry: Telemetry;
  telemetryUiEnabled: boolean;
  showDownloadTelemetry: boolean;
  onToggleDownloadTelemetry: () => void;
};

export function DownloadSection({
  url,
  onUrlChange,
  searchQuery,
  onSearchQueryChange,
  newDownloadTags,
  onNewDownloadTagsChange,
  newDownloadPriority,
  onNewDownloadPriorityChange,
  onSubmit,
  onAddToQueue,
  isDownloadSubmitting,
  lastDownloadStatus,
  onRetryLast,
  downloadTelemetry,
  telemetryUiEnabled,
  showDownloadTelemetry,
  onToggleDownloadTelemetry,
}: Props) {
  const isMegaUrl = /mega\.(nz|co\.nz)/i.test(url.trim());

  return (
    <section className="mb-12" aria-labelledby="add-download-heading">
      <h2 id="add-download-heading" className="sr-only">
        Add download
      </h2>
      <div className="rounded-2xl border border-[var(--ft-border)] bg-[var(--card)] p-1 shadow-md">
        <div className="rounded-[0.875rem] border border-[var(--ft-border-subtle)] bg-[var(--card)] p-6">
          <div className="sr-only" aria-live="polite" aria-atomic="true">
            {isDownloadSubmitting ? 'Working on download or queue request.' : ''}
          </div>
          {lastDownloadStatus && (
            <div
              className={`mb-4 rounded-xl border px-3 py-2 text-xs ${
                lastDownloadStatus.phase === 'failed'
                  ? 'border-[var(--ft-danger)]/40 bg-[var(--ft-danger-bg)] text-[var(--ft-danger)]'
                  : lastDownloadStatus.phase === 'active'
                    ? 'border-[var(--ft-success)]/40 bg-[var(--ft-success-bg)] text-[var(--ft-success)]'
                    : 'border-[var(--ft-warning)]/40 bg-[var(--ft-warning-bg)] text-[var(--ft-warning)]'
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <div className="font-semibold uppercase tracking-wide">
                  Last download: {lastDownloadStatus.phase}
                </div>
                {lastDownloadStatus.phase === 'failed' && (
                  <button
                    type="button"
                    onClick={onRetryLast}
                    className={`rounded-md border border-current/30 px-2 py-1 text-[10px] font-bold uppercase hover:bg-black/5 dark:hover:bg-white/10 ${ftFocusRing}`}
                  >
                    Retry
                  </button>
                )}
              </div>
              <div className="mt-1">{lastDownloadStatus.message}</div>
            </div>
          )}
          {telemetryUiEnabled && (
            <div className="mb-3 rounded-lg border border-[var(--ft-border)] bg-[var(--background)]/60 px-3 py-2 text-[11px] text-[var(--muted-foreground)]">
              <div className="flex items-center justify-between gap-2">
                <span className="font-semibold text-[var(--foreground)]">Download telemetry (debug)</span>
                <button
                  type="button"
                  onClick={onToggleDownloadTelemetry}
                  className={`rounded-md border border-[var(--ft-border)] px-2 py-1 text-[10px] font-bold uppercase tracking-wide hover:bg-[var(--muted)] ${ftFocusRing}`}
                >
                  {showDownloadTelemetry ? 'Hide' : 'Show'}
                </button>
              </div>
              {showDownloadTelemetry && (
                <div className="mt-2 grid grid-cols-1 gap-1 font-mono md:grid-cols-2">
                  <div>clicks={downloadTelemetry.clicks}</div>
                  <div>outcome={downloadTelemetry.lastOutcome}</div>
                  <div>fired_at={downloadTelemetry.lastFiredAt ? new Date(downloadTelemetry.lastFiredAt).toLocaleTimeString() : 'never'}</div>
                  <div>url_len={downloadTelemetry.lastUrlLength}</div>
                  <div>url_type={isMegaUrl ? 'mega' : url.trim() ? 'other' : 'empty'}</div>
                  <div>submitting={isDownloadSubmitting ? 'yes' : 'no'}</div>
                  <div>http_status={downloadTelemetry.lastHttpStatus ?? 'n/a'}</div>
                  <div>from_override={downloadTelemetry.lastWasOverride ? 'yes' : 'no'}</div>
                  <div className="md:col-span-2">last_error={downloadTelemetry.lastErrorMessage || 'none'}</div>
                  <div className="md:col-span-2">
                    last_status={lastDownloadStatus ? `${lastDownloadStatus.phase} at ${new Date(lastDownloadStatus.updatedAt).toLocaleTimeString()}` : 'none'}
                  </div>
                </div>
              )}
            </div>
          )}
          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-4 md:flex-row">
              <div className="relative flex-[2]">
                <label htmlFor="download-url" className="sr-only">
                  MEGA or direct link
                </label>
                <input
                  id="download-url"
                  type="text"
                  value={url}
                  onChange={(e) => onUrlChange(e.target.value)}
                  placeholder="Paste MEGA link or direct https:// download URL…"
                  className={`${ftInput} ${ftFocusRing} py-3.5`}
                />
              </div>
              <div className="relative flex-1">
                <label htmlFor="transfer-search" className="sr-only">
                  Search transfers
                </label>
                <input
                  id="transfer-search"
                  type="search"
                  value={searchQuery}
                  onChange={(e) => onSearchQueryChange(e.target.value)}
                  placeholder="Search transfers…"
                  className={`${ftInput} ${ftFocusRing} py-3.5 pr-10`}
                />
                {searchQuery && (
                  <button
                    type="button"
                    onClick={() => onSearchQueryChange('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-1 text-[var(--muted-foreground)] hover:bg-[var(--muted)]"
                    aria-label="Clear search"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
            <div className="flex flex-col items-center gap-4 md:flex-row">
              <div className="flex flex-1 items-center gap-2 rounded-xl border border-[var(--ft-border)] bg-[var(--background)] px-4 py-2">
                <Tag className="h-4 w-4 text-[var(--muted-foreground)]" aria-hidden />
                <input
                  type="text"
                  value={newDownloadTags}
                  onChange={(e) => onNewDownloadTagsChange(e.target.value)}
                  placeholder="Tags (comma separated)…"
                  className="flex-1 bg-transparent text-sm placeholder:text-[var(--muted-foreground)]/60 focus:outline-none"
                  aria-label="Tags"
                />
              </div>
              <div className="flex items-center gap-2 rounded-xl border border-[var(--ft-border)] bg-[var(--background)] px-4 py-2">
                <span className="text-xs font-bold uppercase text-[var(--muted-foreground)]">Priority</span>
                <select
                  value={newDownloadPriority}
                  onChange={(e) => onNewDownloadPriorityChange(e.target.value as TransferPriority)}
                  className="cursor-pointer bg-transparent text-sm font-bold focus:outline-none"
                  aria-label="Download priority"
                >
                  <option value="LOW">Low</option>
                  <option value="NORMAL">Normal</option>
                  <option value="HIGH">High</option>
                </select>
              </div>
              <div className="ml-auto flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:items-center">
                <button
                  type="button"
                  disabled={isDownloadSubmitting || !url.trim()}
                  onClick={() => onAddToQueue()}
                  className={`flex items-center justify-center gap-2 px-6 py-3 text-sm font-semibold ${ftBtnGhost} ${ftFocusRing}`}
                >
                  Add to queue
                </button>
                <button
                  type="submit"
                  disabled={isDownloadSubmitting || !url.trim()}
                  className={`flex items-center justify-center gap-2 px-8 py-3 ${ftBtnPrimaryLg} ${ftFocusRing}`}
                >
                  {isDownloadSubmitting ? (
                    <RefreshCw className="h-5 w-5 animate-spin" aria-hidden />
                  ) : (
                    <Plus className="h-5 w-5" aria-hidden />
                  )}
                  Download
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
}
