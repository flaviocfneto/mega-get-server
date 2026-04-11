import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from 'react';
import type {FormEvent} from 'react';
import type {
  LogEntry,
  PendingQueueItem,
  Transfer,
  TransferBulkAction,
  TransferPriority,
  TransferState,
} from '../types';
import {
  normalizeBulkPostResponse,
  normalizeDownloadPostResponse,
  normalizePendingQueueItem,
  normalizePendingQueueList,
  normalizeSpeedLimitPostResponse,
  normalizeTransfers,
} from '../apiNormalize';
import {apiDeleteResult, apiGet, apiPostResult, isApiFailure} from '../lib/api';
import {useInterval} from '../hooks/useInterval';
import type {DownloadTelemetryState, LastDownloadStatusState, TransfersSessionValue} from './transfersSessionTypes';

const TransfersSessionContext = createContext<TransfersSessionValue | null>(null);

function useTransfersDomainState(): TransfersSessionValue {
  const historyRefetchRef = useRef<() => void>(() => {});
  const appLoadingRef = useRef<(busy: boolean) => void>(() => {});
  const actionMessageRef = useRef<(msg: string) => void>(() => {});
  const actionErrorRef = useRef<(msg: string) => void>(() => {});

  const registerHistoryRefetch = useCallback((fn: () => void) => {
    historyRefetchRef.current = fn;
  }, []);

  const registerAppLoading = useCallback((fn: (busy: boolean) => void) => {
    appLoadingRef.current = fn;
  }, []);

  const registerActionFeedback = useCallback(
    (handlers: {setMessage: (msg: string) => void; setError: (msg: string) => void}) => {
      actionMessageRef.current = handlers.setMessage;
      actionErrorRef.current = handlers.setError;
    },
    [],
  );

  const triggerHistoryRefetch = useCallback(() => {
    historyRefetchRef.current();
  }, []);

  const [url, setUrl] = useState('');
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [pendingQueue, setPendingQueue] = useState<PendingQueueItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'filename' | 'progress' | 'state'>('filename');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [selectedTransfers, setSelectedTransfers] = useState<Set<string>>(new Set());
  const [filterState, setFilterState] = useState<TransferState | 'ALL'>('ALL');
  const [filterPriority, setFilterPriority] = useState<TransferPriority | 'ALL'>('ALL');
  const [filterLabel, setFilterLabel] = useState<string>('ALL');
  const [newDownloadTags, setNewDownloadTags] = useState('');
  const [newDownloadPriority, setNewDownloadPriority] = useState<TransferPriority>('NORMAL');
  const [isDownloadSubmitting, setIsDownloadSubmitting] = useState(false);
  const [queueActionBusy, setQueueActionBusy] = useState(false);
  const [lastDownloadStatus, setLastDownloadStatus] = useState<LastDownloadStatusState>(null);
  const [downloadTelemetry, setDownloadTelemetry] = useState<DownloadTelemetryState>({
    clicks: 0,
    lastFiredAt: null,
    lastOutcome: 'idle',
    lastUrlLength: 0,
    lastHttpStatus: null,
    lastErrorMessage: null,
    lastWasOverride: false,
  });

  const fetchTransfers = useCallback(async () => {
    try {
      const raw = await apiGet('/api/transfers');
      const data = normalizeTransfers(raw);
      setTransfers(data);
    } catch (err) {
      console.error('Failed to fetch transfers', err);
    }
  }, []);

  const fetchPendingQueue = useCallback(async () => {
    try {
      const data = await apiGet('/api/queue');
      setPendingQueue(normalizePendingQueueList(data));
    } catch (err) {
      console.error('Failed to fetch pending queue', err);
    }
  }, []);

  useInterval(() => {
    void fetchTransfers();
    void fetchPendingQueue();
  }, 1000);

  React.useEffect(() => {
    void fetchTransfers();
    void fetchPendingQueue();
  }, [fetchTransfers, fetchPendingQueue]);

  const applyLogsForDownloadStatus = useCallback((normalized: LogEntry[]) => {
    setLastDownloadStatus((prev) => {
      if (!prev || (prev.phase !== 'submitted' && prev.phase !== 'active')) return prev;
      const messages = normalized.map((l) => l.message);
      const hasStarted = messages.some((m) => m.includes('\u2713 Download started successfully'));
      const failLine = [...messages].reverse().find((m) => m.includes('\u2717 Error'));
      const detailsLine = [...messages].reverse().find((m) => m.startsWith('Details:'));
      if (failLine) {
        return {
          ...prev,
          phase: 'failed' as const,
          message: detailsLine || failLine,
          updatedAt: Date.now(),
        };
      }
      if (hasStarted && prev.phase !== 'active') {
        return {
          ...prev,
          phase: 'active' as const,
          message: 'Download started in MEGAcmd transfer queue.',
          updatedAt: Date.now(),
        };
      }
      return prev;
    });
  }, []);

  const filteredTransfers = useMemo(() => {
    return transfers.filter((t) => {
      const q = (searchQuery || '').toLowerCase();
      const matchesSearch =
        (t.filename || '').toLowerCase().includes(q) ||
        (t.tag || '').includes(searchQuery || '') ||
        (t.url || '').toLowerCase().includes(q);
      const matchesState = filterState === 'ALL' || t.state === filterState;
      const matchesPriority = filterPriority === 'ALL' || t.priority === filterPriority;
      const matchesLabel = filterLabel === 'ALL' || (t.tags && t.tags.includes(filterLabel));
      return matchesSearch && matchesState && matchesPriority && matchesLabel;
    });
  }, [transfers, searchQuery, filterState, filterPriority, filterLabel]);

  const sortedTransfers = useMemo(() => {
    return [...filteredTransfers]
      .filter((t) => t.state !== 'COMPLETED')
      .sort((a, b) => {
        let comparison = 0;
        if (sortBy === 'filename') {
          comparison = a.filename.localeCompare(b.filename);
        } else if (sortBy === 'progress') {
          comparison = a.progress_pct - b.progress_pct;
        } else if (sortBy === 'state') {
          comparison = a.state.localeCompare(b.state);
        }
        return sortOrder === 'asc' ? comparison : -comparison;
      });
  }, [filteredTransfers, sortBy, sortOrder]);

  const completedTransfers = useMemo(
    () => filteredTransfers.filter((t) => t.state === 'COMPLETED'),
    [filteredTransfers],
  );

  const handleDownload = useCallback(
    async (e?: FormEvent, overrideUrl?: string, tags?: string[], priority?: TransferPriority) => {
      e?.preventDefault();
      console.log('handleDownload fired');
      const targetUrl = (overrideUrl || url || '').trim();
      setDownloadTelemetry((prev) => ({
        clicks: prev.clicks + 1,
        lastFiredAt: Date.now(),
        lastOutcome: prev.lastOutcome,
        lastUrlLength: targetUrl.length,
        lastHttpStatus: null,
        lastErrorMessage: null,
        lastWasOverride: !!overrideUrl,
      }));
      if (!targetUrl) {
        setDownloadTelemetry((prev) => ({
          ...prev,
          lastOutcome: 'blocked_no_url',
          lastErrorMessage: 'No URL detected in the download field.',
        }));
        actionErrorRef.current('No URL detected in the download field.');
        return;
      }
      if (!/https?:\/\/(www\.)?mega(\.co)?\.nz\//i.test(targetUrl)) {
        actionErrorRef.current('Only MEGA URLs are allowed.');
        setDownloadTelemetry((prev) => ({
          ...prev,
          lastOutcome: 'failed',
          lastErrorMessage: 'Only MEGA URLs are allowed.',
        }));
        return;
      }

      setIsDownloadSubmitting(true);
      actionErrorRef.current('');
      actionMessageRef.current('');
      try {
        const result = await apiPostResult('/api/download', {
          url: targetUrl,
          tags: tags || [],
          priority: priority || 'NORMAL',
          autostart: true,
        });
        if (!isApiFailure(result)) {
          const data = normalizeDownloadPostResponse(result.data);
          if (!overrideUrl) setUrl('');
          await fetchTransfers();
          triggerHistoryRefetch();
          await fetchPendingQueue();
          actionMessageRef.current(data.message || 'Download submitted.');
          setDownloadTelemetry((prev) => ({
            ...prev,
            lastOutcome: 'submitted',
            lastHttpStatus: result.status,
            lastErrorMessage: null,
          }));
          setLastDownloadStatus({
            phase: 'submitted',
            message: data.message || 'Download submitted to backend.',
            url: targetUrl,
            updatedAt: Date.now(),
          });
        } else {
          const msg = result.message;
          actionErrorRef.current(msg);
          setDownloadTelemetry((prev) => ({
            ...prev,
            lastOutcome: 'failed',
            lastHttpStatus: result.status || null,
            lastErrorMessage: msg,
          }));
          setLastDownloadStatus({
            phase: 'failed',
            message: msg,
            url: targetUrl,
            updatedAt: Date.now(),
          });
        }
      } catch (err) {
        actionErrorRef.current('Download request failed. Check API/MEGAcmd status.');
        setDownloadTelemetry((prev) => ({
          ...prev,
          lastOutcome: 'failed',
          lastHttpStatus: null,
          lastErrorMessage: 'Download request failed before backend confirmation.',
        }));
        setLastDownloadStatus({
          phase: 'failed',
          message: 'Download request failed before backend confirmation.',
          url: targetUrl,
          updatedAt: Date.now(),
        });
        console.error('Download failed', err);
      } finally {
        setIsDownloadSubmitting(false);
      }
    },
    [url, fetchTransfers, fetchPendingQueue, triggerHistoryRefetch],
  );

  const handleAddToQueue = useCallback(async () => {
    const targetUrl = (url || '').trim();
    if (!targetUrl) {
      actionErrorRef.current('No URL detected in the download field.');
      return;
    }
    if (!/https?:\/\/(www\.)?mega(\.co)?\.nz\//i.test(targetUrl)) {
      actionErrorRef.current('Only MEGA URLs are allowed.');
      return;
    }
    setIsDownloadSubmitting(true);
    actionErrorRef.current('');
    actionMessageRef.current('');
    try {
      const tags = newDownloadTags.split(',').map((t) => t.trim()).filter(Boolean);
      const result = await apiPostResult('/api/queue', {
        url: targetUrl,
        tags,
        priority: newDownloadPriority,
      });
      if (!isApiFailure(result)) {
        const src = result.data;
        const item =
          typeof src === 'object' && src !== null && 'item' in src
            ? normalizePendingQueueItem((src as {item: unknown}).item)
            : null;
        setUrl('');
        setNewDownloadTags('');
        setNewDownloadPriority('NORMAL');
        await fetchPendingQueue();
        actionMessageRef.current(item ? `Saved to queue (${item.id.slice(0, 8)}…).` : 'Saved to queue.');
        setLastDownloadStatus({
          phase: 'submitted',
          message: 'Link saved for later. Start it from History and Queue Management on the History and Queue tab.',
          url: targetUrl,
          updatedAt: Date.now(),
        });
      } else {
        actionErrorRef.current(result.message);
        setLastDownloadStatus({
          phase: 'failed',
          message: result.message,
          url: targetUrl,
          updatedAt: Date.now(),
        });
      }
    } catch (err) {
      actionErrorRef.current('Could not add to queue. Check API status.');
      console.error(err);
    } finally {
      setIsDownloadSubmitting(false);
    }
  }, [url, newDownloadTags, newDownloadPriority, fetchPendingQueue]);

  const handleQueueRemove = useCallback(
    async (id: string) => {
      setQueueActionBusy(true);
      actionErrorRef.current('');
      try {
        const result = await apiDeleteResult(`/api/queue/${encodeURIComponent(id)}`);
        if (isApiFailure(result)) actionErrorRef.current(result.message);
        else actionMessageRef.current('Removed from saved queue.');
      } finally {
        setQueueActionBusy(false);
        await fetchPendingQueue();
      }
    },
    [fetchPendingQueue],
  );

  const handleQueueStart = useCallback(
    async (id: string) => {
      setQueueActionBusy(true);
      actionErrorRef.current('');
      try {
        const result = await apiPostResult(`/api/queue/${encodeURIComponent(id)}/start`, {});
        if (isApiFailure(result)) {
          if (result.status === 409 && result.details === 'Queue item is already starting') {
            actionMessageRef.current('This link is already starting.');
          } else {
            actionErrorRef.current(result.message);
          }
        } else {
          actionMessageRef.current('Download started from queue.');
          await fetchTransfers();
        }
      } finally {
        setQueueActionBusy(false);
        await fetchPendingQueue();
      }
    },
    [fetchTransfers, fetchPendingQueue],
  );

  const handleQueueStartNext = useCallback(async () => {
    setQueueActionBusy(true);
    actionErrorRef.current('');
    try {
      const result = await apiPostResult('/api/queue/start-next', {});
      if (isApiFailure(result)) actionErrorRef.current(result.message);
      else {
        actionMessageRef.current('Started next queued link.');
        await fetchTransfers();
      }
    } finally {
      setQueueActionBusy(false);
      await fetchPendingQueue();
    }
  }, [fetchTransfers, fetchPendingQueue]);

  const handleQueueStartAll = useCallback(async () => {
    setQueueActionBusy(true);
    actionErrorRef.current('');
    try {
      const result = await apiPostResult('/api/queue/start-all', {});
      if (isApiFailure(result)) actionErrorRef.current(result.message);
      else {
        actionMessageRef.current('Started batch from queue.');
        await fetchTransfers();
      }
    } finally {
      setQueueActionBusy(false);
      await fetchPendingQueue();
    }
  }, [fetchTransfers, fetchPendingQueue]);

  const handleAction = useCallback(
    async (tag: string, action: 'pause' | 'resume' | 'cancel' | 'retry') => {
      try {
        const result = await apiPostResult(`/api/transfers/${tag}/${action}`);
        if (isApiFailure(result)) {
          actionErrorRef.current(result.message);
          return;
        }
        await fetchTransfers();
        if (action === 'cancel') {
          setSelectedTransfers((prev) => {
            const next = new Set(prev);
            next.delete(tag);
            return next;
          });
        }
      } catch (err) {
        console.error(`Failed to ${action} transfer ${tag}`, err);
      }
    },
    [fetchTransfers],
  );

  const handleSetSpeedLimit = useCallback(
    async (tag: string, limitKbps: number) => {
      try {
        actionErrorRef.current('');
        const result = await apiPostResult(`/api/transfers/${tag}/limit`, {speed_limit_kbps: limitKbps});
        if (isApiFailure(result)) {
          actionErrorRef.current(result.message);
          return;
        }
        const data = normalizeSpeedLimitPostResponse(result.data);
        actionMessageRef.current(data.message || 'Speed limit updated.');
        if (data.applied_to_megacmd === false) {
          actionErrorRef.current('Speed limit saved as UI policy only (not directly enforced by MEGAcmd).');
        }
        await fetchTransfers();
      } catch (err) {
        actionErrorRef.current(`Failed to set speed limit for ${tag}.`);
        console.error(`Failed to set speed limit for ${tag}`, err);
      }
    },
    [fetchTransfers],
  );

  const toggleSelect = useCallback((tag: string) => {
    setSelectedTransfers((prev) => {
      const next = new Set(prev);
      if (next.has(tag)) next.delete(tag);
      else next.add(tag);
      return next;
    });
  }, []);

  const selectAll = useCallback(
    (section: 'active' | 'completed') => {
      const items = section === 'active' ? sortedTransfers : completedTransfers;
      const allSelected = items.every((t) => selectedTransfers.has(t.tag));

      setSelectedTransfers((prev) => {
        const next = new Set(prev);
        if (allSelected) {
          items.forEach((t) => next.delete(t.tag));
        } else {
          items.forEach((t) => next.add(t.tag));
        }
        return next;
      });
    },
    [sortedTransfers, completedTransfers, selectedTransfers],
  );

  const handleBulkAction = useCallback(
    async (action: TransferBulkAction, value?: TransferPriority) => {
      const tags = Array.from(selectedTransfers);
      if (tags.length === 0) return;

      appLoadingRef.current(true);
      actionErrorRef.current('');
      actionMessageRef.current('');
      try {
        if (action === 'redownload') {
          const selectedItems = transfers.filter((t) => selectedTransfers.has(t.tag));
          for (const t of selectedItems) {
            await handleDownload(undefined, t.url, t.tags, t.priority);
          }
        } else {
          const result = await apiPostResult('/api/transfers/bulk', {tags, action, value});
          if (!isApiFailure(result)) {
            const data = normalizeBulkPostResponse(result.data);
            actionMessageRef.current(`Bulk action "${action}" applied to ${data.affectedCount} transfer(s).`);
            if (action === 'remove' || action === 'cancel') {
              setSelectedTransfers(new Set());
            }
          } else {
            actionErrorRef.current(result.message);
          }
        }

        await fetchTransfers();
        triggerHistoryRefetch();
      } catch (err) {
        actionErrorRef.current(`Bulk action ${action} failed.`);
        console.error(`Bulk action ${action} failed`, err);
      } finally {
        setTimeout(() => appLoadingRef.current(false), 500);
      }
    },
    [selectedTransfers, transfers, handleDownload, fetchTransfers, triggerHistoryRefetch],
  );

  return useMemo(
    (): TransfersSessionValue => ({
      url,
      setUrl,
      transfers,
      pendingQueue,
      searchQuery,
      setSearchQuery,
      sortBy,
      setSortBy,
      sortOrder,
      setSortOrder,
      selectedTransfers,
      setSelectedTransfers,
      filterState,
      setFilterState,
      filterPriority,
      setFilterPriority,
      filterLabel,
      setFilterLabel,
      newDownloadTags,
      setNewDownloadTags,
      newDownloadPriority,
      setNewDownloadPriority,
      isDownloadSubmitting,
      queueActionBusy,
      lastDownloadStatus,
      downloadTelemetry,
      sortedTransfers,
      completedTransfers,
      handleDownload,
      handleAddToQueue,
      handleQueueRemove,
      handleQueueStart,
      handleQueueStartNext,
      handleQueueStartAll,
      handleAction,
      handleSetSpeedLimit,
      toggleSelect,
      selectAll,
      handleBulkAction,
      fetchTransfers,
      fetchPendingQueue,
      registerHistoryRefetch,
      registerAppLoading,
      applyLogsForDownloadStatus,
      registerActionFeedback,
    }),
    [
      url,
      transfers,
      pendingQueue,
      searchQuery,
      sortBy,
      sortOrder,
      selectedTransfers,
      filterState,
      filterPriority,
      filterLabel,
      newDownloadTags,
      newDownloadPriority,
      isDownloadSubmitting,
      queueActionBusy,
      lastDownloadStatus,
      downloadTelemetry,
      sortedTransfers,
      completedTransfers,
      handleDownload,
      handleAddToQueue,
      handleQueueRemove,
      handleQueueStart,
      handleQueueStartNext,
      handleQueueStartAll,
      handleAction,
      handleSetSpeedLimit,
      toggleSelect,
      selectAll,
      handleBulkAction,
      fetchTransfers,
      fetchPendingQueue,
      registerHistoryRefetch,
      registerAppLoading,
      applyLogsForDownloadStatus,
      registerActionFeedback,
    ],
  );
}

export function TransfersSessionProvider({children}: {children: React.ReactNode}) {
  const value = useTransfersDomainState();
  return <TransfersSessionContext.Provider value={value}>{children}</TransfersSessionContext.Provider>;
}

export function useTransfersSession(): TransfersSessionValue {
  const ctx = useContext(TransfersSessionContext);
  if (!ctx) {
    throw new Error('useTransfersSession must be used within TransfersSessionProvider');
  }
  return ctx;
}
