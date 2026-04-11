import type {Dispatch, SetStateAction} from 'react';
import type {FormEvent} from 'react';
import type {
  LogEntry,
  PendingQueueItem,
  Transfer,
  TransferBulkAction,
  TransferPriority,
  TransferState,
} from '../types';

export type LastDownloadStatusState = {
  phase: 'submitted' | 'active' | 'failed';
  message: string;
  url: string;
  updatedAt: number;
} | null;

export type DownloadTelemetryState = {
  clicks: number;
  lastFiredAt: number | null;
  lastOutcome: 'idle' | 'submitted' | 'failed' | 'blocked_no_url';
  lastUrlLength: number;
  lastHttpStatus: number | null;
  lastErrorMessage: string | null;
  lastWasOverride: boolean;
};

/** Public surface for `useTransfersSession()` and test overrides. */
export interface TransfersSessionValue {
  url: string;
  setUrl: Dispatch<SetStateAction<string>>;
  transfers: Transfer[];
  pendingQueue: PendingQueueItem[];
  searchQuery: string;
  setSearchQuery: Dispatch<SetStateAction<string>>;
  sortBy: 'filename' | 'progress' | 'state';
  setSortBy: Dispatch<SetStateAction<'filename' | 'progress' | 'state'>>;
  sortOrder: 'asc' | 'desc';
  setSortOrder: Dispatch<SetStateAction<'asc' | 'desc'>>;
  selectedTransfers: Set<string>;
  setSelectedTransfers: Dispatch<SetStateAction<Set<string>>>;
  filterState: TransferState | 'ALL';
  setFilterState: Dispatch<SetStateAction<TransferState | 'ALL'>>;
  filterPriority: TransferPriority | 'ALL';
  setFilterPriority: Dispatch<SetStateAction<TransferPriority | 'ALL'>>;
  filterLabel: string;
  setFilterLabel: Dispatch<SetStateAction<string>>;
  newDownloadTags: string;
  setNewDownloadTags: Dispatch<SetStateAction<string>>;
  newDownloadPriority: TransferPriority;
  setNewDownloadPriority: Dispatch<SetStateAction<TransferPriority>>;
  isDownloadSubmitting: boolean;
  queueActionBusy: boolean;
  lastDownloadStatus: LastDownloadStatusState;
  downloadTelemetry: DownloadTelemetryState;
  sortedTransfers: Transfer[];
  completedTransfers: Transfer[];
  handleDownload: (
    e?: FormEvent,
    overrideUrl?: string,
    tags?: string[],
    priority?: TransferPriority,
  ) => Promise<void>;
  handleAddToQueue: () => Promise<void>;
  handleQueueRemove: (id: string) => Promise<void>;
  handleQueueStart: (id: string) => Promise<void>;
  handleQueueStartNext: () => Promise<void>;
  handleQueueStartAll: () => Promise<void>;
  handleAction: (tag: string, action: 'pause' | 'resume' | 'cancel' | 'retry') => Promise<void>;
  handleSetSpeedLimit: (tag: string, limitKbps: number) => Promise<void>;
  toggleSelect: (tag: string) => void;
  selectAll: (section: 'active' | 'completed') => void;
  handleBulkAction: (action: TransferBulkAction, value?: TransferPriority) => Promise<void>;
  fetchTransfers: () => Promise<void>;
  fetchPendingQueue: () => Promise<void>;
  /** App registers `fetchHistory` so download/bulk flows can refresh history. */
  registerHistoryRefetch: (fn: () => void) => void;
  /** Optional: maps bulk-action busy state to App `isLoading` (login spinner) for parity with previous behavior. */
  registerAppLoading: (fn: (busy: boolean) => void) => void;
  /** Called from App after log fetch to advance last-download UI from log lines. */
  applyLogsForDownloadStatus: (logs: LogEntry[]) => void;
  /** App wires global banner setters so download/queue/bulk flows can surface messages. */
  registerActionFeedback: (handlers: {setMessage: (msg: string) => void; setError: (msg: string) => void}) => void;
}
