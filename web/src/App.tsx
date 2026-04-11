import React, { useState, useEffect, useLayoutEffect, useRef, useMemo, useCallback } from 'react';
import {
  Plus,
  Pause,
  Play,
  X,
  Settings,
  Timer,
  Gauge,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Clock,
  RefreshCw,
  RotateCcw,
  DownloadCloud,
  User,
  LogIn,
  HardDrive,
  Activity,
  Zap,
  BarChart3,
  ArrowUpDown,
  ShieldCheck,
  LogOut,
  History,
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import {
  AppConfig,
  HistoryItem,
  AccountInfo,
  LogEntry,
  LogLevel,
  LogCategory,
  AnalyticsData,
  ToolDiagnosticsReport,
  TerminalHistoryEntry,
} from './types';
import {
  mergeAppConfig,
  normalizeHistory,
  normalizeLogs,
  normalizeAccountInfo,
  normalizeAnalytics,
  normalizeToolDiagnostics,
  normalizeLoginPostResponse,
  normalizeTerminalPostResponse,
} from './apiNormalize';
import { formatBytes, formatETA, quotaBarWidthPct, quotaPercent } from './lib/format';
import { copyToClipboard } from './lib/clipboard';
import { accountTypeLabel } from './lib/accountLabels';
import {apiDeleteResult, apiGet, apiPost, apiPostResult, isApiFailure} from './lib/api';
import { useThemePreference } from './hooks/useThemePreference';
import {useInterval} from './hooks/useInterval';
import { AppHeader } from './components/AppHeader';
import { BottomNav } from './components/shell/BottomNav';
import { SidebarNav } from './components/shell/SidebarNav';
import type { AppSectionId } from './navigation/primaryNav';
import { ToolDiagnosticsPanel } from './components/ToolDiagnosticsPanel';
import { DownloadSection } from './components/DownloadSection';
import { TransfersView } from './views/TransfersView';
import { HistoryView } from './views/HistoryView';
import { AnalyticsView } from './views/AnalyticsView';
import { SystemConsoleView } from './views/SystemConsoleView';
import { buildAppHash, parseAppHash } from './navigation/urlSections';
import { ftBtnPrimaryLg, ftBtnPrimaryMd, ftBtnPrimarySm, ftFocusRing, ftInput, ftInputMuted } from './lib/ftUi';
import { useTransfersSession } from './context/TransfersSessionContext';

export default function App() {
  const readStoredBoolean = (key: string, fallback: boolean): boolean => {
    if (typeof window === 'undefined') return fallback;
    const raw = window.localStorage.getItem(key);
    if (raw === null) return fallback;
    if (raw === '1' || raw === 'true') return true;
    if (raw === '0' || raw === 'false') return false;
    return fallback;
  };

  const TELEMETRY_VISIBILITY_KEY = 'ft_download_telemetry_visible';
  const TELEMETRY_UI_ENABLED_KEY = 'ft_download_telemetry_ui_enabled';
  const {
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
    registerHistoryRefetch,
    registerAppLoading,
    applyLogsForDownloadStatus,
    registerActionFeedback,
  } = useTransfersSession();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeSection, setActiveSection] = useState<AppSectionId>('transfers');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [tempPath, setTempPath] = useState('');
  const [tempLimit, setTempLimit] = useState<number>(3);
  const [tempHistoryLimit, setTempHistoryLimit] = useState<number>(50);
  const [tempRetentionDays, setTempRetentionDays] = useState<number>(7);
  const [tempMaxRetries, setTempMaxRetries] = useState<number>(3);
  const [tempGlobalSpeedLimit, setTempGlobalSpeedLimit] = useState<number>(0);
  const [tempScheduledStart, setTempScheduledStart] = useState<string>('00:00');
  const [tempScheduledStop, setTempScheduledStop] = useState<string>('23:59');
  const [tempSchedulingEnabled, setTempSchedulingEnabled] = useState<boolean>(false);
  const [tempSoundAlertsEnabled, setTempSoundAlertsEnabled] = useState<boolean>(true);
  const [tempPrivacyMode, setTempPrivacyMode] = useState<boolean>(false);
  const [tempCompactMode, setTempCompactMode] = useState<boolean>(false);
  const [tempPostAction, setTempPostAction] = useState<string>('');
  const [tempWebhookUrl, setTempWebhookUrl] = useState<string>('');
  const [tempWatchEnabled, setTempWatchEnabled] = useState<boolean>(false);
  const [tempWatchPath, setTempWatchPath] = useState<string>('');
  const [isDragging, setIsDragging] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [selectedHistory, setSelectedHistory] = useState<Set<string>>(new Set());
  const [logFilterLevel, setLogFilterLevel] = useState<LogLevel | 'ALL'>('ALL');
  const [logFilterCategory, setLogFilterCategory] = useState<LogCategory | 'ALL'>('ALL');
  const [logSearchQuery, setLogSearchQuery] = useState('');
  const [historySearchQuery, setHistorySearchQuery] = useState('');
  const [accountInfo, setAccountInfo] = useState<AccountInfo | null>(null);
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [terminalInput, setTerminalInput] = useState('');
  const [terminalOutput, setTerminalOutput] = useState<TerminalHistoryEntry[]>([]);
  const [isTerminalOpen, setIsTerminalOpen] = useState(false);
  const [actionMessage, setActionMessage] = useState('');
  const [actionError, setActionError] = useState('');
  const [toolDiagnostics, setToolDiagnostics] = useState<ToolDiagnosticsReport | null>(null);
  const [isDiagnosticsLoading, setIsDiagnosticsLoading] = useState(false);
  const [showDownloadTelemetry, setShowDownloadTelemetry] = useState<boolean>(() => {
    return readStoredBoolean(TELEMETRY_VISIBILITY_KEY, false);
  });
  const [telemetryUiEnabled, setTelemetryUiEnabled] = useState<boolean>(() => {
    return readStoredBoolean(TELEMETRY_UI_ENABLED_KEY, true);
  });
  const {theme, toggleTheme} = useThemePreference();

  const notifiedTagsRef = useRef<Set<string>>(new Set());

  const logEndRef = useRef<HTMLDivElement>(null);
  const terminalEndRef = useRef<HTMLDivElement>(null);
  const sectionFocusSkipFirst = useRef(true);

  const handleSelectSection = (id: AppSectionId) => {
    setActiveSection(id);
    if (id === 'system') setIsTerminalOpen(false);
  };

  useLayoutEffect(() => {
    const p = parseAppHash(window.location.hash);
    setActiveSection(p.section);
    setIsTerminalOpen(p.section === 'system' && p.systemTab === 'terminal');
  }, []);

  useEffect(() => {
    const onHashChange = () => {
      const p = parseAppHash(window.location.hash);
      setActiveSection(p.section);
      setIsTerminalOpen(p.section === 'system' && p.systemTab === 'terminal');
    };
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  useEffect(() => {
    const systemTab = isTerminalOpen ? 'terminal' : 'log';
    const next = buildAppHash(activeSection, systemTab);
    const current = window.location.hash || '#/transfers';
    if (current !== next) {
      window.history.replaceState(
        null,
        '',
        `${window.location.pathname}${window.location.search}${next}`,
      );
    }
  }, [activeSection, isTerminalOpen]);

  useEffect(() => {
    if (sectionFocusSkipFirst.current) {
      sectionFocusSkipFirst.current = false;
      return;
    }
    document.getElementById('main-content')?.focus({ preventScroll: true });
  }, [activeSection]);

  useEffect(() => {
    if (activeSection !== 'system' || !isTerminalOpen) return;
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalOutput, activeSection, isTerminalOpen]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(TELEMETRY_VISIBILITY_KEY, showDownloadTelemetry ? '1' : '0');
  }, [showDownloadTelemetry, TELEMETRY_VISIBILITY_KEY]);
  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(TELEMETRY_UI_ENABLED_KEY, telemetryUiEnabled ? '1' : '0');
  }, [telemetryUiEnabled, TELEMETRY_UI_ENABLED_KEY]);
  useEffect(() => {
    if (!telemetryUiEnabled && showDownloadTelemetry) {
      setShowDownloadTelemetry(false);
    }
  }, [telemetryUiEnabled, showDownloadTelemetry]);
  useEffect(() => {
    if ("Notification" in window) {
      if (Notification.permission === "granted") {
        setNotificationsEnabled(true);
      } else if (Notification.permission !== "denied") {
        Notification.requestPermission().then(permission => {
          setNotificationsEnabled(permission === "granted");
        });
      }
    }
  }, []);

  const sendNotification = (title: string, body: string) => {
    if (notificationsEnabled && "Notification" in window) {
      new Notification(title, { body, icon: '/icons/ft-icon-app.svg' });
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const text = e.dataTransfer.getData('text');
    if (text && (text.includes('mega.nz') || text.includes('mega.co.nz'))) {
      setUrl(text);
      handleSelectSection('transfers');
      handleDownload(undefined, text);
    }
  };

  useEffect(() => {
    fetchConfig();
    fetchHistory();
    fetchLogs();
    fetchAccount();
    fetchAnalytics();
    fetchToolDiagnostics();
  }, []);

  useInterval(() => {
    fetchLogs();
    fetchAccount();
    fetchAnalytics();
  }, 1000);

  useInterval(() => {
    fetchToolDiagnostics();
  }, 15000);

  useEffect(() => {
    if (activeSection === 'system' && !isTerminalOpen) {
      scrollToBottom();
    }
  }, [logs, activeSection, isTerminalOpen]);

  const scrollToBottom = () => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchConfig = async () => {
    try {
      const raw = await apiGet('/api/config');
      const data = mergeAppConfig(raw);
      setConfig(data);
      setTempPath(data.download_dir);
      setTempLimit(data.transfer_limit);
      setTempHistoryLimit(data.history_limit);
      setTempRetentionDays(data.history_retention_days);
      setTempMaxRetries(data.max_retries);
      setTempGlobalSpeedLimit(data.global_speed_limit_kbps);
      setTempScheduledStart(data.scheduled_start ?? '00:00');
      setTempScheduledStop(data.scheduled_stop ?? '23:59');
      setTempSchedulingEnabled(data.is_scheduling_enabled);
      setTempSoundAlertsEnabled(data.sound_alerts_enabled);
      setTempPrivacyMode(data.is_privacy_mode ?? false);
      setTempCompactMode(data.is_compact_mode ?? false);
      setTempPostAction(data.post_download_action ?? '');
      setTempWebhookUrl(data.webhook_url ?? '');
      setTempWatchEnabled(data.watch_folder_enabled ?? false);
      setTempWatchPath(data.watch_folder_path ?? '');
    } catch (err) {
      console.error('Failed to fetch config', err);
    }
  };

  const updateConfigInState = (raw: unknown) => {
    const data = mergeAppConfig(raw);
    setTempPath(data.download_dir);
    setTempLimit(data.transfer_limit);
    setTempHistoryLimit(data.history_limit);
    setTempRetentionDays(data.history_retention_days);
    setTempMaxRetries(data.max_retries);
    setTempGlobalSpeedLimit(data.global_speed_limit_kbps);
    setTempScheduledStart(data.scheduled_start ?? '00:00');
    setTempScheduledStop(data.scheduled_stop ?? '23:59');
    setTempSchedulingEnabled(data.is_scheduling_enabled);
    setTempSoundAlertsEnabled(data.sound_alerts_enabled);
    setTempPrivacyMode(data.is_privacy_mode ?? false);
    setTempCompactMode(data.is_compact_mode ?? false);
    setTempPostAction(data.post_download_action ?? '');
    setTempWebhookUrl(data.webhook_url ?? '');
    setTempWatchEnabled(data.watch_folder_enabled ?? false);
    setTempWatchPath(data.watch_folder_path ?? '');
  };

  const updateConfig = async (updates: Partial<AppConfig>) => {
    try {
      const raw = await apiPost('/api/config', updates);
      const data = mergeAppConfig(raw);
      setConfig((prev) => (prev ? { ...prev, ...data } : data));
      updateConfigInState(raw);
    } catch (err) {
      console.error('Failed to update config', err);
    }
  };

  const playAlert = () => {
    if (config?.sound_alerts_enabled) {
      const audio = new Audio('https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3');
      audio.play().catch(e => console.error('Failed to play alert sound', e));
    }
  };

  const fetchHistory = useCallback(async () => {
    try {
      const data = await apiGet('/api/history');
      setHistory(normalizeHistory(data));
    } catch (err) {
      console.error('Failed to fetch history', err);
    }
  }, []);

  useEffect(() => {
    registerHistoryRefetch(() => {
      void fetchHistory();
    });
  }, [registerHistoryRefetch, fetchHistory]);

  useEffect(() => {
    registerAppLoading(setIsLoading);
  }, [registerAppLoading]);

  useEffect(() => {
    registerActionFeedback({
      setMessage: setActionMessage,
      setError: setActionError,
    });
  }, [registerActionFeedback]);

  useEffect(() => {
    transfers.forEach((t) => {
      if (!notifiedTagsRef.current.has(t.tag)) {
        if (t.state === 'COMPLETED') {
          sendNotification('Download Completed', `Finished: ${t.filename}`);
          playAlert();
          notifiedTagsRef.current.add(t.tag);
        } else if (t.state === 'FAILED') {
          sendNotification('Download Failed', `Error downloading: ${t.filename}`);
          notifiedTagsRef.current.add(t.tag);
        }
      }
    });
  }, [transfers, notificationsEnabled, config]);

  const fetchAccount = async () => {
    try {
      const raw = await apiGet('/api/account');
      const data = normalizeAccountInfo(raw);
      setAccountInfo(data);
    } catch (err) {
      console.error('Failed to fetch account info', err);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const raw = await apiGet('/api/analytics');
      const data = normalizeAnalytics(raw);
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to fetch analytics', err);
    }
  };


  const fetchToolDiagnostics = async () => {
    try {
      setIsDiagnosticsLoading(true);
      const raw = await apiGet('/api/diag/tools');
      const data = normalizeToolDiagnostics(raw);
      setToolDiagnostics(data);
    } catch (err) {
      console.error('Failed to fetch tool diagnostics', err);
    } finally {
      setIsDiagnosticsLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setActionError('');
    setActionMessage('');
    try {
      const result = await apiPostResult('/api/login', { email: loginEmail, password: loginPassword });
      if (isApiFailure(result)) {
        setActionError(result.message);
        console.error('Login failed', result.message);
      } else {
        const data = normalizeLoginPostResponse(result.data);
        if (data.status === 'success') {
          setAccountInfo(data.account ?? null);
          setIsLoginOpen(false);
          setLoginEmail('');
          setLoginPassword('');
          setActionMessage(data.message || 'Login successful.');
        } else {
          const msg = data.message || 'Login failed.';
          setActionError(msg);
          console.error('Login failed', msg);
        }
      }
    } catch (err) {
      setActionError('Login request failed. Check API/MEGAcmd status.');
      console.error('Login failed', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await apiPostResult('/api/logout');
      setAccountInfo(null);
      fetchAccount();
    } catch (err) {
      console.error('Logout failed', err);
    }
  };

  const executeCommand = async (cmd?: string) => {
    const commandToExecute = cmd || terminalInput;
    if (!commandToExecute.trim()) return;
    const source: TerminalHistoryEntry['source'] = cmd ? 'preset' : 'manual';

    try {
      setActionError('');
      const result = await apiPostResult('/api/terminal', { command: commandToExecute });
      if (isApiFailure(result)) {
        setActionError(result.message);
        return;
      }
      const data = normalizeTerminalPostResponse(result.data);
      if (data.output === 'TERMINAL_CLEAR') {
        setTerminalOutput([]);
      } else {
        setTerminalOutput((prev) => [
          ...prev,
          {cmd: commandToExecute, out: data.output ?? '', source},
        ]);
      }
      if (!cmd) setTerminalInput('');
      if (data.ok) {
        setActionMessage(`Terminal command executed (exit ${data.exit_code ?? 0}).`);
      } else {
        setActionError(data.output || data.blocked_reason || 'Terminal command failed.');
      }
    } catch (error) {
      setActionError('Terminal command failed.');
      console.error('Terminal error:', error);
    }
  };

  const fetchLogs = async () => {
    try {
      const data = await apiGet('/api/logs');
      const normalized = normalizeLogs(data);
      setLogs(normalized);
      applyLogsForDownloadStatus(normalized);
    } catch (err) {
      console.error('Failed to fetch logs', err);
    }
  };

  const handleInstallCommand = async (cmd: string) => {
    await copyToClipboard(cmd);
    setActionMessage('Install command copied. Paste and run it in your system terminal.');
    setActionError('');
  };

  const handleCancelAll = async () => {
    try {
      await apiPostResult('/api/transfers/cancel-all');
      fetchTransfers();
    } catch (err) {
      console.error('Failed to cancel all transfers', err);
    }
  };

  const clearHistory = async () => {
    try {
      const result = await apiDeleteResult('/api/history');
      if (isApiFailure(result)) {
        const { message } = result;
        setActionError(message);
        return;
      }
      setHistory([]);
      setSelectedHistory(new Set());
    } catch (err) {
      console.error('Failed to clear history', err);
    }
  };

  const exportLogs = () => {
    const text = logs.map((l) => `[${l.timestamp}] ${l.level} ${l.category}: ${l.message}`).join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `megaget-logs-${new Date().toISOString()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const exportHistory = () => {
    const blob = new Blob([JSON.stringify(history, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `megaget-history-${new Date().toISOString()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const clearLogs = async () => {
    try {
      setActionError('');
      const result = await apiDeleteResult('/api/logs');
      if (isApiFailure(result)) {
        const { message } = result;
        setActionError(message);
        return;
      }
      await fetchLogs();
      setActionMessage('Logs cleared on server.');
    } catch (err) {
      setActionError('Failed to clear logs.');
      console.error('Failed to clear logs', err);
    }
  };

  const clearTerminalOutput = () => setTerminalOutput([]);

  const filteredHistory = history.filter((h) =>
    (h.url || '').toLowerCase().includes((historySearchQuery || '').toLowerCase()),
  );

  const filteredLogs = logs.filter((log) => {
    const q = (logSearchQuery || '').toLowerCase();
    const matchesSearch =
      (log.message || '').toLowerCase().includes(q) || (log.tag && log.tag.includes(logSearchQuery || ''));
    const matchesLevel = logFilterLevel === 'ALL' || log.level === logFilterLevel;
    const matchesCategory = logFilterCategory === 'ALL' || log.category === logFilterCategory;
    return matchesSearch && matchesLevel && matchesCategory;
  });

  const queueSummary = useMemo(() => {
    const active = transfers.filter((t) => t.state === 'ACTIVE').length;
    const queued = transfers.filter((t) => t.state === 'QUEUED').length;
    const failed = transfers.filter((t) => t.state === 'FAILED' || t.state === 'RETRYING').length;
    return `${active} active, ${queued} queued, ${failed} need attention`;
  }, [transfers]);

  return (
    <div 
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className="relative flex min-h-screen flex-col bg-[var(--background)] font-sans text-[var(--foreground)] transition-colors duration-300 selection:bg-[color-mix(in_srgb,var(--ft-accent)_28%,transparent)]"
    >
      <a
        href="#main-content"
        className={`sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[200] focus:rounded-md focus:border focus:border-[var(--ft-border)] focus:bg-[var(--card)] focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:shadow-md ${ftFocusRing}`}
      >
        Skip to main content
      </a>
      <div role="status" aria-live="polite" aria-atomic="true" className="sr-only">
        {queueSummary}
      </div>
      <AnimatePresence>
        {isDragging && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="pointer-events-none fixed inset-0 z-[100] m-4 flex items-center justify-center rounded-3xl border-4 border-dashed border-[color-mix(in_srgb,var(--ft-accent)_55%,var(--ft-border))] bg-[color-mix(in_srgb,var(--ft-accent)_12%,transparent)] backdrop-blur-md"
          >
            <div className="flex flex-col items-center gap-4 rounded-2xl bg-[var(--card)] p-8 shadow-2xl">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--ft-accent)] animate-bounce">
                <Plus className="h-8 w-8 text-[var(--ft-accent-fg)]" />
              </div>
              <p className="text-xl font-bold text-[var(--foreground)]">Drop a link to tug files into your queue</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      <AppHeader
        config={config}
        accountInfo={accountInfo}
        theme={theme}
        toggleTheme={toggleTheme}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenLogin={() => setIsLoginOpen(true)}
        onLogout={handleLogout}
      />

      <div className="flex min-h-0 flex-1">
        <SidebarNav activeId={activeSection} onSelect={handleSelectSection} />
        <div className="flex min-w-0 flex-1 flex-col">
          <main
            id="main-content"
            className="mx-auto w-full max-w-7xl px-4 py-8 pb-[calc(3.5rem+env(safe-area-inset-bottom,0px))] lg:pb-8"
            tabIndex={-1}
          >
        {(actionMessage || actionError) && (
          <div
            className={`mb-4 rounded-lg border px-3 py-2 text-sm ${
              actionError
                ? 'border-rose-500/40 text-rose-400 bg-rose-500/10'
                : 'border-emerald-500/40 text-emerald-400 bg-emerald-500/10'
            }`}
          >
            {actionError || actionMessage}
          </div>
        )}

        {activeSection === 'transfers' && (
          <div className="grid grid-cols-1 gap-8">
            <DownloadSection
              url={url}
              onUrlChange={setUrl}
              searchQuery={searchQuery}
              onSearchQueryChange={setSearchQuery}
              newDownloadTags={newDownloadTags}
              onNewDownloadTagsChange={setNewDownloadTags}
              newDownloadPriority={newDownloadPriority}
              onNewDownloadPriorityChange={setNewDownloadPriority}
              onSubmit={(e) => {
                e.preventDefault();
                handleDownload(
                  e,
                  undefined,
                  newDownloadTags.split(',').map((t) => t.trim()).filter(Boolean),
                  newDownloadPriority,
                );
                setNewDownloadTags('');
                setNewDownloadPriority('NORMAL');
              }}
              onAddToQueue={handleAddToQueue}
              isDownloadSubmitting={isDownloadSubmitting}
              lastDownloadStatus={lastDownloadStatus}
              onRetryLast={() => lastDownloadStatus && handleDownload(undefined, lastDownloadStatus.url)}
              downloadTelemetry={downloadTelemetry}
              telemetryUiEnabled={telemetryUiEnabled}
              showDownloadTelemetry={showDownloadTelemetry}
              onToggleDownloadTelemetry={() => setShowDownloadTelemetry((prev) => !prev)}
            />
            <TransfersView
              transfers={transfers}
              sortedTransfers={sortedTransfers}
              completedTransfers={completedTransfers}
              config={config}
              selectedTransfers={selectedTransfers}
              toggleSelect={toggleSelect}
              selectAll={selectAll}
              handleBulkAction={handleBulkAction}
              handleAction={handleAction}
              handleSetSpeedLimit={handleSetSpeedLimit}
              handleDownload={handleDownload}
              filterState={filterState}
              setFilterState={setFilterState}
              filterPriority={filterPriority}
              setFilterPriority={setFilterPriority}
              filterLabel={filterLabel}
              setFilterLabel={setFilterLabel}
              sortBy={sortBy}
              setSortBy={setSortBy}
              sortOrder={sortOrder}
              setSortOrder={setSortOrder}
              setSelectedTransfers={setSelectedTransfers}
            />
          </div>
        )}
        {activeSection === 'history' && (
          <HistoryView
            history={history}
            filteredHistory={filteredHistory}
            historySearchQuery={historySearchQuery}
            setHistorySearchQuery={setHistorySearchQuery}
            selectedHistory={selectedHistory}
            setSelectedHistory={setSelectedHistory}
            setUrl={(next) => {
              setUrl(next);
              handleSelectSection('transfers');
            }}
            exportHistory={exportHistory}
            clearHistory={clearHistory}
            pendingQueue={pendingQueue}
            queuePanelBusy={queueActionBusy}
            onQueueRemove={handleQueueRemove}
            onQueueStart={handleQueueStart}
            onQueueStartNext={handleQueueStartNext}
            onQueueStartAll={handleQueueStartAll}
          />
        )}
        {activeSection === 'analytics' && <AnalyticsView analytics={analytics} />}
        {activeSection === 'system' && (
          <SystemConsoleView
            isTerminalOpen={isTerminalOpen}
            setIsTerminalOpen={setIsTerminalOpen}
            filteredLogs={filteredLogs}
            logFilterLevel={logFilterLevel}
            setLogFilterLevel={setLogFilterLevel}
            logFilterCategory={logFilterCategory}
            setLogFilterCategory={setLogFilterCategory}
            logSearchQuery={logSearchQuery}
            setLogSearchQuery={setLogSearchQuery}
            exportLogs={exportLogs}
            clearLogs={clearLogs}
            terminalOutput={terminalOutput}
            terminalInput={terminalInput}
            setTerminalInput={setTerminalInput}
            executeCommand={executeCommand}
            clearTerminalOutput={clearTerminalOutput}
            terminalEndRef={terminalEndRef}
            logEndRef={logEndRef}
            config={config}
            updateConfig={updateConfig}
          />
        )}

          </main>
        </div>
      </div>

      <BottomNav activeId={activeSection} onSelect={handleSelectSection} />

      {/* Login Modal */}
      <AnimatePresence>
        {isLoginOpen && (
          <div className="fixed inset-0 z-[110] flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsLoginOpen(false)}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            />
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-labelledby="login-modal-title"
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-md bg-[var(--card)] border border-[var(--border)] rounded-3xl shadow-2xl overflow-hidden"
            >
              <div className="flex items-center justify-between px-8 py-6 border-b border-[var(--border)]">
                <div className="flex items-center gap-3">
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-xl"
                    style={{background: 'color-mix(in srgb, var(--ft-accent) 14%, var(--ft-surface))'}}
                  >
                    <User className="h-5 w-5 text-[var(--ft-accent)]" aria-hidden />
                  </div>
                  <h2 id="login-modal-title" className="text-xl font-bold">
                    Login to MEGA
                  </h2>
                </div>
                <button 
                  onClick={() => setIsLoginOpen(false)}
                  className="p-2 hover:bg-[var(--muted)] rounded-xl text-[var(--muted-foreground)] transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleLogin} className="p-8 space-y-6" aria-labelledby="login-modal-title">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-[var(--muted-foreground)] uppercase tracking-widest">Email Address</label>
                    <input
                      type="email"
                      required
                      value={loginEmail}
                      onChange={(e) => setLoginEmail(e.target.value)}
                      placeholder="your@email.com"
                      className={`${ftInput} ${ftFocusRing}`}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-[var(--muted-foreground)] uppercase tracking-widest">Password</label>
                    <input
                      type="password"
                      required
                      value={loginPassword}
                      onChange={(e) => setLoginPassword(e.target.value)}
                      placeholder="••••••••"
                      className={`${ftInput} ${ftFocusRing}`}
                    />
                  </div>
                </div>

                <div className="rounded-2xl border border-[var(--ft-border)] bg-[color-mix(in_srgb,var(--ft-accent)_6%,var(--card))] p-4">
                  <p className="text-[11px] text-[var(--muted-foreground)] leading-relaxed">
                    Your credentials are used only to authenticate with MEGAcmd. We do not store your password on our servers.
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className={`w-full ${ftBtnPrimaryLg} ${ftFocusRing} py-4 active:scale-[0.98]`}
                >
                  {isLoading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <LogIn className="w-5 h-5" />}
                  Login
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Settings Modal */}
      <AnimatePresence>
        {isSettingsOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsSettingsOpen(false)}
              className="absolute inset-0 z-0 bg-black/60 backdrop-blur-sm"
            />
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-labelledby="settings-modal-title"
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative z-10 flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-3xl border border-[var(--border)] bg-[var(--card)] shadow-2xl"
            >
              <div className="flex shrink-0 items-center justify-between border-b border-[var(--border)] px-8 py-6">
                <div className="flex items-center gap-3">
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-xl"
                    style={{background: 'color-mix(in srgb, var(--ft-accent) 14%, var(--ft-surface))'}}
                  >
                    <Settings className="h-5 w-5 text-[var(--ft-accent)]" aria-hidden />
                  </div>
                  <h2 id="settings-modal-title" className="text-xl font-bold">
                    Advanced Settings
                  </h2>
                </div>
                <button 
                  onClick={() => setIsSettingsOpen(false)}
                  className="p-2 hover:bg-[var(--muted)] rounded-xl transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="min-h-0 flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar">
                {/* General Settings */}
                <div className="space-y-4">
                  <h3 className="text-sm font-bold uppercase tracking-widest text-[var(--muted-foreground)] flex items-center gap-2">
                    <DownloadCloud className="w-4 h-4" />
                    General
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-xs font-medium text-[var(--muted-foreground)]">Download Directory</label>
                      <input
                        type="text"
                        value={tempPath}
                        onChange={(e) => setTempPath(e.target.value)}
                        className={`${ftInputMuted} ${ftFocusRing}`}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-medium text-[var(--muted-foreground)]">Concurrent Transfer Limit</label>
                      <input
                        type="number"
                        value={tempLimit}
                        onChange={(e) => setTempLimit(parseInt(e.target.value) || 1)}
                        className={`${ftInputMuted} ${ftFocusRing}`}
                      />
                    </div>
                  </div>
                </div>

                {toolDiagnostics && (
                  <ToolDiagnosticsPanel
                    report={toolDiagnostics}
                    loading={isDiagnosticsLoading}
                    onRefresh={fetchToolDiagnostics}
                    onInstallCommand={handleInstallCommand}
                  />
                )}

                {/* Speed & Retries */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold uppercase tracking-widest text-[var(--muted-foreground)] flex items-center gap-2">
                      <Gauge className="w-4 h-4" />
                      Performance
                    </h3>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold uppercase text-[var(--muted-foreground)]">Sound Alerts</span>
                      <button
                        onClick={() => setTempSoundAlertsEnabled(!tempSoundAlertsEnabled)}
                        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none ${tempSoundAlertsEnabled ? 'bg-[var(--ft-accent)]' : 'bg-[var(--muted)]'}`}
                      >
                        <span className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${tempSoundAlertsEnabled ? 'translate-x-5' : 'translate-x-1'}`} />
                      </button>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-xs font-medium text-[var(--muted-foreground)]">Global Speed Limit (KB/s)</label>
                      <div className="flex items-center gap-3">
                        <input
                          type="number"
                          value={tempGlobalSpeedLimit}
                          onChange={(e) => setTempGlobalSpeedLimit(parseInt(e.target.value) || 0)}
                          className={`flex-1 ${ftInputMuted} ${ftFocusRing}`}
                        />
                        <span className="text-xs text-[var(--muted-foreground)] w-20">{tempGlobalSpeedLimit === 0 ? 'Unlimited' : `${(tempGlobalSpeedLimit / 1024).toFixed(1)} MB/s`}</span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-medium text-[var(--muted-foreground)]">Max Auto-Retries</label>
                      <input
                        type="number"
                        value={tempMaxRetries}
                        onChange={(e) => setTempMaxRetries(parseInt(e.target.value) || 0)}
                        className={`${ftInputMuted} ${ftFocusRing}`}
                      />
                    </div>
                  </div>
                </div>

                {/* Scheduling */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold uppercase tracking-widest text-[var(--muted-foreground)] flex items-center gap-2">
                      <Timer className="w-4 h-4" />
                      Scheduling
                    </h3>
                    <button
                      onClick={() => setTempSchedulingEnabled(!tempSchedulingEnabled)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${tempSchedulingEnabled ? 'bg-[var(--ft-accent)]' : 'bg-[var(--muted)]'}`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${tempSchedulingEnabled ? 'translate-x-6' : 'translate-x-1'}`} />
                    </button>
                  </div>
                  <div className={`grid grid-cols-1 md:grid-cols-2 gap-6 transition-opacity ${tempSchedulingEnabled ? 'opacity-100' : 'opacity-40 pointer-events-none'}`}>
                    <div className="space-y-2">
                      <label className="text-xs font-medium text-[var(--muted-foreground)]">Start Time</label>
                      <input
                        type="time"
                        value={tempScheduledStart}
                        onChange={(e) => setTempScheduledStart(e.target.value)}
                        className={`${ftInputMuted} ${ftFocusRing}`}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-medium text-[var(--muted-foreground)]">Stop Time</label>
                      <input
                        type="time"
                        value={tempScheduledStop}
                        onChange={(e) => setTempScheduledStop(e.target.value)}
                        className={`${ftInputMuted} ${ftFocusRing}`}
                      />
                    </div>
                  </div>
                </div>

                {/* History Settings */}
                <div className="space-y-4">
                  <h3 className="text-sm font-bold uppercase tracking-widest text-[var(--muted-foreground)] flex items-center gap-2">
                    <History className="w-4 h-4" />
                    History
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-xs font-medium text-[var(--muted-foreground)]">Max History Entries</label>
                      <input
                        type="number"
                        value={tempHistoryLimit}
                        onChange={(e) => setTempHistoryLimit(parseInt(e.target.value) || 0)}
                        className={`${ftInputMuted} ${ftFocusRing}`}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-medium text-[var(--muted-foreground)]">Retention (Days)</label>
                      <input
                        type="number"
                        value={tempRetentionDays}
                        onChange={(e) => setTempRetentionDays(parseInt(e.target.value) || 0)}
                        className={`${ftInputMuted} ${ftFocusRing}`}
                      />
                    </div>
                  </div>
                </div>

                {/* Automation Settings */}
                <div className="space-y-4 pt-8 border-t border-[var(--border)]">
                  <h3 className="text-sm font-bold uppercase tracking-widest text-[var(--muted-foreground)]/60 flex items-center gap-2">
                    <Zap className="w-4 h-4" />
                    Automation
                  </h3>
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label className="text-xs font-medium text-[var(--muted-foreground)]">Post-Download Action (Shell Command)</label>
                        <input
                          type="text"
                          value={tempPostAction}
                          onChange={(e) => setTempPostAction(e.target.value)}
                          placeholder="e.g. mv {file} /nas/completed/"
                          className={`${ftInputMuted} ${ftFocusRing}`}
                        />
                        <p className="text-[10px] text-[var(--muted-foreground)]/60 italic">Use {'{file}'} as placeholder for filename</p>
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-medium text-[var(--muted-foreground)]">Webhook URL (POST)</label>
                        <input
                          type="text"
                          value={tempWebhookUrl}
                          onChange={(e) => setTempWebhookUrl(e.target.value)}
                          placeholder="https://hooks.example.com/..."
                          className={`${ftInputMuted} ${ftFocusRing}`}
                        />
                      </div>
                    </div>

                    <div className="p-4 bg-[var(--muted)]/20 rounded-2xl border border-[var(--border)] space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex flex-col gap-1">
                          <span className="text-sm font-bold">Watch Folder</span>
                          <span className="text-[10px] text-[var(--muted-foreground)]">Automatically queue links from files in a directory</span>
                        </div>
                        <button 
                          onClick={() => setTempWatchEnabled(!tempWatchEnabled)}
                          className={`w-12 h-6 rounded-full transition-all relative ${tempWatchEnabled ? 'bg-[var(--ft-accent)]' : 'bg-[var(--muted)]'}`}
                        >
                          <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${tempWatchEnabled ? 'right-1' : 'left-1'}`} />
                        </button>
                      </div>
                      {tempWatchEnabled && (
                        <div className="space-y-2 pt-2 border-t border-[var(--border)]/50">
                          <label className="text-xs font-medium text-[var(--muted-foreground)]">Watch Path</label>
                          <input
                            type="text"
                            value={tempWatchPath}
                            onChange={(e) => setTempWatchPath(e.target.value)}
                            className={`${ftInput} py-2 ${ftFocusRing}`}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Interface Settings */}
                <div className="space-y-4 pt-8 border-t border-[var(--border)]">
                  <h3 className="text-sm font-bold uppercase tracking-widest text-[var(--muted-foreground)]/60 flex items-center gap-2">
                    <Activity className="w-4 h-4" />
                    Interface & Privacy
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="flex items-center justify-between p-4 bg-[var(--muted)]/20 rounded-2xl border border-[var(--border)]">
                      <div className="flex flex-col gap-1">
                        <span className="text-sm font-bold">Privacy Mode</span>
                        <span className="text-[10px] text-[var(--muted-foreground)]">Mask filenames and URLs</span>
                      </div>
                      <button 
                        onClick={() => {
                          const val = !tempPrivacyMode;
                          setTempPrivacyMode(val);
                          updateConfig({ is_privacy_mode: val });
                        }}
                        className={`w-12 h-6 rounded-full transition-all relative ${tempPrivacyMode ? 'bg-[var(--ft-accent)]' : 'bg-[var(--muted)]'}`}
                      >
                        <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${tempPrivacyMode ? 'right-1' : 'left-1'}`} />
                      </button>
                    </div>
                    <div className="flex items-center justify-between p-4 bg-[var(--muted)]/20 rounded-2xl border border-[var(--border)]">
                      <div className="flex flex-col gap-1">
                        <span className="text-sm font-bold">Compact Mode</span>
                        <span className="text-[10px] text-[var(--muted-foreground)]">High-density transfer list</span>
                      </div>
                      <button 
                        onClick={() => {
                          const val = !tempCompactMode;
                          setTempCompactMode(val);
                          updateConfig({ is_compact_mode: val });
                        }}
                        className={`w-12 h-6 rounded-full transition-all relative ${tempCompactMode ? 'bg-[var(--ft-accent)]' : 'bg-[var(--muted)]'}`}
                      >
                        <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${tempCompactMode ? 'right-1' : 'left-1'}`} />
                      </button>
                    </div>
                    <div className="flex items-center justify-between p-4 bg-[var(--muted)]/20 rounded-2xl border border-[var(--border)]">
                      <div className="flex flex-col gap-1">
                        <span className="text-sm font-bold">Download Debug Telemetry</span>
                        <span className="text-[10px] text-[var(--muted-foreground)]">Show or fully hide telemetry panel and toggle</span>
                      </div>
                      <button
                        onClick={() => setTelemetryUiEnabled((prev) => !prev)}
                        className={`w-12 h-6 rounded-full transition-all relative ${telemetryUiEnabled ? 'bg-[var(--ft-accent)]' : 'bg-[var(--muted)]'}`}
                        aria-label="Toggle download debug telemetry"
                      >
                        <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${telemetryUiEnabled ? 'right-1' : 'left-1'}`} />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Account Settings */}
                <div className="space-y-4 pt-8 border-t border-[var(--border)]">
                  <h3 className="text-sm font-bold uppercase tracking-widest text-[var(--muted-foreground)] flex items-center gap-2">
                    <User className="w-4 h-4" />
                    Account
                  </h3>
                  {accountInfo?.is_logged_in ? (
                    <div className="bg-[var(--muted)]/30 border border-[var(--border)] rounded-2xl p-6 space-y-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div
                            className="flex h-12 w-12 items-center justify-center rounded-full"
                            style={{background: 'color-mix(in srgb, var(--ft-accent) 14%, var(--ft-surface))'}}
                          >
                            <User className="h-6 w-6 text-[var(--ft-accent)]" aria-hidden />
                          </div>
                          <div>
                            <p className={`text-sm font-bold text-[var(--foreground)] ${config?.is_privacy_mode ? 'blur-sm select-none' : ''}`}>{accountInfo.email}</p>
                            <p className="mt-0.5 flex items-center gap-1 text-[10px] font-bold uppercase tracking-widest text-[var(--ft-accent)]">
                              <ShieldCheck className="h-3 w-3" aria-hidden />
                              {accountTypeLabel(accountInfo.account_type)} Account
                            </p>
                          </div>
                        </div>
                        <button 
                          onClick={handleLogout}
                          className="px-4 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 rounded-xl text-xs font-bold transition-all"
                        >
                          Logout
                        </button>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Storage Usage */}
                        <div className="space-y-3">
                          <div className="flex items-center justify-between text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-wider">
                            <div className="flex items-center gap-2">
                              <HardDrive className="h-3.5 w-3.5 text-[var(--ft-accent)]" aria-hidden />
                              Storage Usage
                            </div>
                            <span>{quotaPercent(accountInfo.storage_used_bytes, accountInfo.storage_total_bytes)}%</span>
                          </div>
                          <div className="w-full h-2 bg-[var(--background)] rounded-full overflow-hidden border border-[var(--border)]">
                            <motion.div 
                              initial={{ width: 0 }}
                              animate={{ width: `${quotaBarWidthPct(accountInfo.storage_used_bytes, accountInfo.storage_total_bytes)}%` }}
                              className="h-full bg-[var(--ft-accent)]"
                            />
                          </div>
                          <div className="flex justify-between text-[9px] text-[var(--muted-foreground)]/60 font-mono">
                            <span>{formatBytes(accountInfo.storage_used_bytes)} used</span>
                            <span>{formatBytes(accountInfo.storage_total_bytes)} total</span>
                          </div>
                        </div>

                        {/* Bandwidth Usage (settings only when quota is available) */}
                        {accountInfo.bandwidth_limit_bytes > 0 && (
                          <div className="space-y-3">
                            <div className="flex items-center justify-between text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-wider">
                              <div className="flex items-center gap-2">
                                <ArrowUpDown className="h-3.5 w-3.5 text-[var(--ft-accent)]" aria-hidden />
                                Bandwidth Quota
                              </div>
                              <span>{quotaPercent(accountInfo.bandwidth_used_bytes, accountInfo.bandwidth_limit_bytes)}%</span>
                            </div>
                            <div className="w-full h-2 bg-[var(--background)] rounded-full overflow-hidden border border-[var(--border)]">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${quotaBarWidthPct(accountInfo.bandwidth_used_bytes, accountInfo.bandwidth_limit_bytes)}%` }}
                                className="h-full bg-[var(--ft-accent)]"
                              />
                            </div>
                            <div className="flex justify-between text-[9px] text-[var(--muted-foreground)]/60 font-mono">
                              <span>{formatBytes(accountInfo.bandwidth_used_bytes)} used</span>
                              <span>{formatBytes(accountInfo.bandwidth_limit_bytes)} total</span>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="bg-[var(--muted)]/30 border border-[var(--border)] rounded-2xl p-8 text-center space-y-4">
                      <div className="w-16 h-16 bg-[var(--background)] rounded-full flex items-center justify-center mx-auto border border-[var(--border)]">
                        <User className="w-8 h-8 text-[var(--muted-foreground)]/40" />
                      </div>
                      <div>
                        <p className="text-sm font-bold text-[var(--foreground)]">Not Logged In</p>
                        <p className="text-xs text-[var(--muted-foreground)] mt-1">Login to your MEGA account to manage your storage and bandwidth.</p>
                      </div>
                      <button 
                        onClick={() => {
                          setIsSettingsOpen(false);
                          setIsLoginOpen(true);
                        }}
                        className={`${ftBtnPrimaryMd} text-xs ${ftFocusRing}`}
                      >
                        Login to MEGA
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex shrink-0 items-center justify-end gap-4 border-t border-[var(--border)] bg-[var(--muted)]/30 p-8">
                <button
                  onClick={() => setIsSettingsOpen(false)}
                  className="px-6 py-2.5 rounded-xl text-sm font-bold text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    updateConfig({
                      download_dir: tempPath,
                      transfer_limit: tempLimit,
                      history_limit: tempHistoryLimit,
                      history_retention_days: tempRetentionDays,
                      max_retries: tempMaxRetries,
                      global_speed_limit_kbps: tempGlobalSpeedLimit,
                      scheduled_start: tempScheduledStart,
                      scheduled_stop: tempScheduledStop,
                      is_scheduling_enabled: tempSchedulingEnabled,
                      sound_alerts_enabled: tempSoundAlertsEnabled,
                      is_privacy_mode: tempPrivacyMode,
                      is_compact_mode: tempCompactMode,
                      post_download_action: tempPostAction,
                      webhook_url: tempWebhookUrl,
                      watch_folder_enabled: tempWatchEnabled,
                      watch_folder_path: tempWatchPath
                    });
                    setIsSettingsOpen(false);
                  }}
                  className={`rounded-xl active:scale-95 ${ftBtnPrimaryMd} ${ftFocusRing}`}
                >
                  Save Changes
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
