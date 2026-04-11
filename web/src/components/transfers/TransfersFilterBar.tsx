import {Filter, SortAsc, SortDesc, Tag} from 'lucide-react';
import type {TransferPriority, TransferState} from '../../types';
import {ftFocusRing} from '../../lib/ftUi';

type Props = {
  filterState: TransferState | 'ALL';
  onFilterState: (v: TransferState | 'ALL') => void;
  filterPriority: TransferPriority | 'ALL';
  onFilterPriority: (v: TransferPriority | 'ALL') => void;
  filterLabel: string;
  onFilterLabel: (v: string) => void;
  sortBy: 'filename' | 'progress' | 'state';
  onSortBy: (v: 'filename' | 'progress' | 'state') => void;
  sortOrder: 'asc' | 'desc';
  onToggleSortOrder: () => void;
  onClearFilters: () => void;
};

export function TransfersFilterBar({
  filterState,
  onFilterState,
  filterPriority,
  onFilterPriority,
  filterLabel,
  onFilterLabel,
  sortBy,
  onSortBy,
  sortOrder,
  onToggleSortOrder,
  onClearFilters,
}: Props) {
  const hasFilters =
    filterState !== 'ALL' || filterPriority !== 'ALL' || (filterLabel && filterLabel !== 'ALL');

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
      <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2 rounded-xl border border-[var(--ft-border)] bg-[var(--muted)]/40 p-1">
        <Filter className="ml-2 h-3 w-3 shrink-0 text-[var(--muted-foreground)]" aria-hidden />
        <label htmlFor="filter-state" className="sr-only">
          Filter by state
        </label>
        <select
          id="filter-state"
          value={filterState}
          onChange={(e) => onFilterState(e.target.value as TransferState | 'ALL')}
          className={`cursor-pointer border-r border-[var(--ft-border)] bg-transparent px-2 py-1.5 text-[10px] font-bold uppercase text-[var(--muted-foreground)] focus:outline-none ${ftFocusRing}`}
        >
          <option value="ALL">All states</option>
          <option value="ACTIVE">Active</option>
          <option value="QUEUED">Queued</option>
          <option value="PAUSED">Paused</option>
          <option value="FAILED">Failed</option>
        </select>
        <label htmlFor="filter-priority" className="sr-only">
          Filter by priority
        </label>
        <select
          id="filter-priority"
          value={filterPriority}
          onChange={(e) => onFilterPriority(e.target.value as TransferPriority | 'ALL')}
          className={`cursor-pointer border-r border-[var(--ft-border)] bg-transparent px-2 py-1.5 text-[10px] font-bold uppercase text-[var(--muted-foreground)] focus:outline-none ${ftFocusRing}`}
        >
          <option value="ALL">All priorities</option>
          <option value="HIGH">High</option>
          <option value="NORMAL">Normal</option>
          <option value="LOW">Low</option>
        </select>
        <div className="flex items-center gap-2 px-2">
          <Tag className="h-3 w-3 text-[var(--muted-foreground)]" aria-hidden />
          <label htmlFor="filter-tag" className="sr-only">
            Filter by tag
          </label>
          <input
            id="filter-tag"
            type="text"
            value={filterLabel === 'ALL' ? '' : filterLabel}
            onChange={(e) => onFilterLabel(e.target.value || 'ALL')}
            placeholder="Tag…"
            className="w-24 bg-transparent text-[10px] font-bold uppercase text-[var(--muted-foreground)] placeholder:text-[var(--muted-foreground)]/40 focus:outline-none"
          />
        </div>
      </div>
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1 rounded-xl border border-[var(--ft-border)] bg-[var(--muted)]/40 p-1">
          <label htmlFor="sort-by" className="sr-only">
            Sort by
          </label>
          <select
            id="sort-by"
            value={sortBy}
            onChange={(e) => onSortBy(e.target.value as 'filename' | 'progress' | 'state')}
            className={`cursor-pointer bg-transparent px-2 py-1.5 text-[10px] font-bold uppercase text-[var(--muted-foreground)] focus:outline-none ${ftFocusRing}`}
          >
            <option value="filename">Name</option>
            <option value="progress">Progress</option>
            <option value="state">State</option>
          </select>
          <button
            type="button"
            onClick={onToggleSortOrder}
            className={`rounded-lg p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--border)] ${ftFocusRing}`}
            title={`Sort ${sortOrder === 'asc' ? 'descending' : 'ascending'}`}
          >
            {sortOrder === 'asc' ? <SortAsc className="h-3 w-3" /> : <SortDesc className="h-3 w-3" />}
          </button>
        </div>
        {hasFilters && (
          <button
            type="button"
            onClick={onClearFilters}
            className={`text-[10px] font-bold uppercase text-[var(--ft-accent)] hover:underline ${ftFocusRing} rounded px-2 py-1`}
          >
            Clear filters
          </button>
        )}
      </div>
    </div>
  );
}
