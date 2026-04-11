import {AnimatePresence, motion, useReducedMotion} from 'motion/react';
import type {FormEvent} from 'react';
import {
  CheckCircle2,
  CheckSquare,
  CloudDownload,
  Download,
  Square,
  X,
} from 'lucide-react';
import type {AppConfig, Transfer, TransferBulkAction, TransferPriority, TransferState} from '../types';
import {formatBytes} from '../lib/format';
import {ftFocusRing} from '../lib/ftUi';
import {TransfersKpiRow} from '../components/transfers/TransfersKpiRow';
import {TransfersFilterBar} from '../components/transfers/TransfersFilterBar';
import {TransfersBulkBar} from '../components/transfers/TransfersBulkBar';
import {TransferRowCard} from '../components/transfers/TransferRowCard';
type Props = {
  transfers: Transfer[];
  sortedTransfers: Transfer[];
  completedTransfers: Transfer[];
  config: AppConfig | null;
  selectedTransfers: Set<string>;
  toggleSelect: (tag: string) => void;
  selectAll: (section: 'active' | 'completed') => void;
  handleBulkAction: (action: TransferBulkAction, value?: TransferPriority) => void;
  handleAction: (tag: string, action: 'pause' | 'resume' | 'cancel' | 'retry') => void;
  handleSetSpeedLimit: (tag: string, limitKbps: number) => void;
  handleDownload: (e?: FormEvent, overrideUrl?: string, tags?: string[], priority?: TransferPriority) => void;
  filterState: TransferState | 'ALL';
  setFilterState: (v: TransferState | 'ALL') => void;
  filterPriority: TransferPriority | 'ALL';
  setFilterPriority: (v: TransferPriority | 'ALL') => void;
  filterLabel: string;
  setFilterLabel: (v: string) => void;
  sortBy: 'filename' | 'progress' | 'state';
  setSortBy: (v: 'filename' | 'progress' | 'state') => void;
  sortOrder: 'asc' | 'desc';
  setSortOrder: (v: 'asc' | 'desc') => void;
  setSelectedTransfers: (s: Set<string>) => void;
};

export function TransfersView({
  transfers,
  sortedTransfers,
  completedTransfers,
  config,
  selectedTransfers,
  toggleSelect,
  selectAll,
  handleBulkAction,
  handleAction,
  handleSetSpeedLimit,
  handleDownload,
  pendingQueue,
  queuePanelBusy,
  onQueueRemove,
  onQueueStart,
  onQueueStartNext,
  onQueueStartAll,
  filterState,
  setFilterState,
  filterPriority,
  setFilterPriority,
  filterLabel,
  setFilterLabel,
  sortBy,
  setSortBy,
  sortOrder,
  setSortOrder,
  setSelectedTransfers,
}: Props) {
  const reduceMotion = !!useReducedMotion();

  return (
    <div className="space-y-6">
      <h1 className="sr-only">Transfers</h1>
      <TransfersKpiRow transfers={transfers} />

      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-[var(--foreground)]">
            <button
              type="button"
              onClick={() => selectAll('active')}
              className={`rounded p-1 text-[var(--muted-foreground)] hover:bg-[var(--muted)] ${ftFocusRing}`}
              title="Select all active"
            >
              {sortedTransfers.length > 0 && sortedTransfers.every((t) => selectedTransfers.has(t.tag)) ? (
                <CheckSquare className="h-5 w-5 text-[var(--ft-accent)]" aria-hidden />
              ) : (
                <Square className="h-5 w-5" aria-hidden />
              )}
            </button>
            Active transfers
            <span className="rounded-full border border-[var(--ft-border)] bg-[var(--muted)] px-2 py-0.5 text-[10px] text-[var(--muted-foreground)]">
              {sortedTransfers.length}
            </span>
          </h2>
        </div>

        <TransfersFilterBar
          filterState={filterState}
          onFilterState={setFilterState}
          filterPriority={filterPriority}
          onFilterPriority={setFilterPriority}
          filterLabel={filterLabel}
          onFilterLabel={setFilterLabel}
          sortBy={sortBy}
          onSortBy={setSortBy}
          sortOrder={sortOrder}
          onToggleSortOrder={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
          onClearFilters={() => {
            setFilterState('ALL');
            setFilterPriority('ALL');
            setFilterLabel('ALL');
          }}
        />

        <TransfersBulkBar
          count={selectedTransfers.size}
          onPause={() => handleBulkAction('pause')}
          onResume={() => handleBulkAction('resume')}
          onCancel={() => handleBulkAction('cancel')}
          onRedownload={() => handleBulkAction('redownload')}
          onSetPriority={(p) => handleBulkAction('set_priority', p as TransferPriority)}
          onDeselectAll={() => setSelectedTransfers(new Set())}
        />
      </div>

      <div className="space-y-4">
        <AnimatePresence mode="popLayout">
          {sortedTransfers.length === 0 ? (
            <motion.div
              initial={reduceMotion ? false : {opacity: 0}}
              animate={{opacity: 1}}
              className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-[var(--ft-border)] bg-[var(--card)] py-20 text-[var(--muted-foreground)]"
            >
              <CloudDownload className="mb-4 h-12 w-12 opacity-20" aria-hidden />
              <p className="text-sm">No active transfers</p>
              <p className="mt-1 text-xs text-[var(--muted-foreground)]">Paste a link above to add to the queue</p>
            </motion.div>
          ) : (
            sortedTransfers.map((t) => (
              <div key={t.tag}>
                <TransferRowCard
                  transfer={t}
                  config={config}
                  selected={selectedTransfers.has(t.tag)}
                  onToggleSelect={() => toggleSelect(t.tag)}
                  onAction={(a) => handleAction(t.tag, a)}
                  onSetSpeedLimit={(kbps) => handleSetSpeedLimit(t.tag, kbps)}
                  reduceMotion={reduceMotion}
                />
              </div>
            ))
          )}
        </AnimatePresence>
      </div>

      {completedTransfers.length > 0 && (
        <div className="border-t border-[var(--ft-border)] pt-8">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-[var(--foreground)]">
              <button
                type="button"
                onClick={() => selectAll('completed')}
                className={`rounded p-1 text-[var(--muted-foreground)] hover:bg-[var(--muted)] ${ftFocusRing}`}
                title="Select all completed"
              >
                {completedTransfers.every((t) => selectedTransfers.has(t.tag)) ? (
                  <CheckSquare className="h-5 w-5 text-[var(--ft-accent)]" aria-hidden />
                ) : (
                  <Square className="h-5 w-5" aria-hidden />
                )}
              </button>
              Completed
              <CheckCircle2 className="h-4 w-4 text-[var(--ft-success)]" aria-hidden />
              <span className="rounded-full border border-[var(--ft-success)]/35 bg-[var(--ft-success-bg)] px-2 py-0.5 text-[10px] font-bold text-[var(--ft-success)]">
                {completedTransfers.length}
              </span>
            </h2>
          </div>
          <div className="space-y-3">
            {completedTransfers.map((t) => (
              <div
                key={t.tag}
                className={`flex items-center justify-between gap-4 rounded-xl border p-4 transition-all ${
                  selectedTransfers.has(t.tag)
                    ? 'border-[var(--ft-accent)] opacity-100 ring-1 ring-[color-mix(in_srgb,var(--ft-accent)_25%,transparent)]'
                    : 'border-[var(--ft-border)] opacity-80 hover:opacity-100'
                } bg-[var(--card)]`}
              >
                <div className="flex min-w-0 flex-1 items-center gap-3">
                  <button
                    type="button"
                    onClick={() => toggleSelect(t.tag)}
                    className={`rounded p-1 text-[var(--muted-foreground)] hover:bg-[var(--muted)] ${ftFocusRing}`}
                    aria-pressed={selectedTransfers.has(t.tag)}
                  >
                    {selectedTransfers.has(t.tag) ? (
                      <CheckSquare className="h-5 w-5 text-[var(--ft-accent)]" />
                    ) : (
                      <Square className="h-5 w-5" />
                    )}
                  </button>
                  <div className="min-w-0 flex-1">
                    <h3 className="truncate text-sm font-medium text-[var(--foreground)]">{t.filename}</h3>
                    <p className="mt-0.5 font-mono text-[10px] text-[var(--muted-foreground)]">{t.path}</p>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-3">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--ft-success)]">
                    {t.size_bytes === 0 ? 'Unknown size' : formatBytes(t.size_bytes)}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleDownload(undefined, t.url)}
                    className={`rounded-lg p-1.5 text-[var(--muted-foreground)] hover:bg-[color-mix(in_srgb,var(--ft-accent)_12%,transparent)] hover:text-[var(--ft-accent)] ${ftFocusRing}`}
                    title="Download again"
                  >
                    <Download className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleAction(t.tag, 'cancel')}
                    className={`rounded-lg p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--muted)] ${ftFocusRing}`}
                    title="Remove from list"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
