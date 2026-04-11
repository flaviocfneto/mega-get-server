import type {Dispatch, SetStateAction} from 'react';
import {CheckSquare, DownloadCloud, History, Plus, Square, Trash2, X} from 'lucide-react';
import type {HistoryItem, PendingQueueItem} from '../types';
import {ftFocusRing} from '../lib/ftUi';
import {PendingQueuePanel} from '../components/transfers/PendingQueuePanel';

type Props = {
  history: HistoryItem[];
  filteredHistory: HistoryItem[];
  historySearchQuery: string;
  setHistorySearchQuery: (v: string) => void;
  selectedHistory: Set<string>;
  setSelectedHistory: Dispatch<SetStateAction<Set<string>>>;
  setUrl: (v: string) => void;
  exportHistory: () => void;
  clearHistory: () => void;
  pendingQueue: PendingQueueItem[];
  queuePanelBusy: boolean;
  onQueueRemove: (id: string) => void;
  onQueueStart: (id: string) => void;
  onQueueStartNext: () => void;
  onQueueStartAll: () => void;
};

export function HistoryView({
  history,
  filteredHistory,
  historySearchQuery,
  setHistorySearchQuery,
  selectedHistory,
  setSelectedHistory,
  setUrl,
  exportHistory,
  clearHistory,
  pendingQueue,
  queuePanelBusy,
  onQueueRemove,
  onQueueStart,
  onQueueStartNext,
  onQueueStartAll,
}: Props) {
  return (
    <div className="space-y-6">
      <PendingQueuePanel
        items={pendingQueue}
        busy={queuePanelBusy}
        onRemove={onQueueRemove}
        onStart={onQueueStart}
        onStartNext={onQueueStartNext}
        onStartAll={onQueueStartAll}
        title="History and Queue Management"
        headingLevel="h1"
      />

      <div className="mb-2 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-[var(--foreground)]">
          Download History
          <History className="h-4 w-4 text-[var(--muted-foreground)]" aria-hidden />
        </h2>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={exportHistory}
            className={`rounded-lg p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[var(--ft-accent)] ${ftFocusRing}`}
            title="Export history"
          >
            <DownloadCloud className="h-4 w-4" />
          </button>
          {history.length > 0 && (
            <button
              type="button"
              onClick={clearHistory}
              className="flex items-center gap-1 text-[10px] font-bold uppercase text-[var(--muted-foreground)] transition-colors hover:text-[var(--ft-danger)]"
            >
              <Trash2 className="h-3 w-3" aria-hidden />
              {selectedHistory.size > 0 ? 'Clear selected' : 'Clear all'}
            </button>
          )}
        </div>
      </div>

      <div className="relative mb-4">
        <label htmlFor="history-search" className="sr-only">
          Search history
        </label>
        <input
          id="history-search"
          type="search"
          value={historySearchQuery}
          onChange={(e) => setHistorySearchQuery(e.target.value)}
          placeholder="Search history…"
          className={`w-full rounded-xl border border-[var(--ft-border)] bg-[var(--card)] px-4 py-2 text-xs text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--ft-accent)_40%,transparent)]`}
        />
        {historySearchQuery && (
          <button
            type="button"
            onClick={() => setHistorySearchQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-1 text-[var(--muted-foreground)] hover:bg-[var(--muted)]"
            aria-label="Clear history search"
          >
            <X className="h-3 w-3" />
          </button>
        )}
      </div>

      <div className={`overflow-hidden rounded-2xl border border-[var(--ft-border)] bg-[var(--card)] shadow-sm`}>
        {filteredHistory.length === 0 ? (
          <div className="p-8 text-center text-sm italic text-[var(--muted-foreground)]">
            {historySearchQuery ? 'No matches' : 'No history yet'}
          </div>
        ) : (
          <div className="divide-y divide-[var(--ft-border)]">
            {filteredHistory.map((h, i) => (
              <div key={`${h.url}-${i}`} className="group flex items-center">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedHistory((prev) => {
                      const next = new Set(prev);
                      if (next.has(h.url)) next.delete(h.url);
                      else next.add(h.url);
                      return next;
                    });
                  }}
                  className={`p-4 transition-colors hover:bg-[var(--muted)] ${
                    selectedHistory.has(h.url) ? 'text-[var(--ft-accent)]' : 'text-[var(--muted-foreground)]/40'
                  }`}
                  aria-pressed={selectedHistory.has(h.url)}
                >
                  {selectedHistory.has(h.url) ? (
                    <CheckSquare className="h-4 w-4" aria-hidden />
                  ) : (
                    <Square className="h-4 w-4" aria-hidden />
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setUrl(h.url)}
                  className="flex min-w-0 flex-1 items-center justify-between gap-3 py-4 pr-4 text-left transition-colors hover:bg-[var(--muted)]"
                >
                  <div className="flex min-w-0 flex-col">
                    <span className="truncate text-xs text-[var(--muted-foreground)] transition-colors group-hover:text-[var(--ft-accent)]">
                      {h.url}
                    </span>
                    <span className="mt-1 text-[9px] text-[var(--muted-foreground)]/50">
                      {new Date(h.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <Plus className="h-3 w-3 shrink-0 text-[var(--muted-foreground)]/40 group-hover:text-[var(--ft-accent)]" aria-hidden />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
