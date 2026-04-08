import React, { useState, useEffect, useRef } from 'react';
import { 
  CloudDownload, 
  Plus, 
  Pause, 
  Play, 
  X, 
  Settings,
  Timer,
  Gauge,
  History, 
  Terminal, 
  ChevronDown, 
  ChevronUp,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Clock,
  RefreshCw,
  RotateCcw,
  Sun,
  Moon,
  ArrowUpDown,
  SortAsc,
  SortDesc,
  Download,
  Square,
  CheckSquare,
  Copy,
  FileText,
  Filter,
  Tag,
  DownloadCloud,
  User,
  LogOut,
  LogIn,
  ShieldCheck,
  HardDrive,
  Send,
  Command,
  Activity,
  Zap,
  BarChart3
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { Transfer, AppConfig, HistoryItem, AccountInfo, TransferState, TransferPriority, LogEntry, LogLevel, LogCategory, AnalyticsData, ToolDiagnosticsReport } from './types';
import { mergeAppConfig, normalizeHistory, normalizeLogs } from './apiNormalize';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar
} from 'recharts';

function quotaPercent(used: number, limit: number): number {
  if (!Number.isFinite(used) || !Number.isFinite(limit) || limit <= 0) return 0;
  return Math.min(100, Math.round((used / limit) * 100));
}

function quotaBarWidthPct(used: number, limit: number): number {
  if (!Number.isFinite(used) || !Number.isFinite(limit) || limit <= 0) return 0;
  return Math.min(100, (used / limit) * 100);
}

function accountTypeLabel(accountType: AccountInfo['account_type']): string {
  if (accountType === 'UNKNOWN') return 'MEGA';
  return accountType;
}

export default function App() {
  const [url, setUrl] = useState('');
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [isLogExpanded, setIsLogExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isDownloadSubmitting, setIsDownloadSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState<'transfers' | 'history' | 'analytics'>('transfers');
  const [isEditingPath, setIsEditingPath] = useState(false);
  const [isEditingLimit, setIsEditingLimit] = useState(false);
  const [isEditingHistoryLimit, setIsEditingHistoryLimit] = useState(false);
  const [isEditingRetention, setIsEditingRetention] = useState(false);
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
  const [searchQuery, setSearchQuery] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [sortBy, setSortBy] = useState<'filename' | 'progress' | 'state'>('filename');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [selectedTransfers, setSelectedTransfers] = useState<Set<string>>(new Set());
  const [selectedHistory, setSelectedHistory] = useState<Set<string>>(new Set());
  const [filterState, setFilterState] = useState<TransferState | 'ALL'>('ALL');
  const [filterPriority, setFilterPriority] = useState<TransferPriority | 'ALL'>('ALL');
  const [filterLabel, setFilterLabel] = useState<string>('ALL');
  const [logFilterLevel, setLogFilterLevel] = useState<LogLevel | 'ALL'>('ALL');
  const [logFilterCategory, setLogFilterCategory] = useState<LogCategory | 'ALL'>('ALL');
  const [logSearchQuery, setLogSearchQuery] = useState('');
  const [historySearchQuery, setHistorySearchQuery] = useState('');
  const [accountInfo, setAccountInfo] = useState<AccountInfo | null>(null);
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [newDownloadTags, setNewDownloadTags] = useState('');
  const [newDownloadPriority, setNewDownloadPriority] = useState<TransferPriority>('NORMAL');
  const [terminalInput, setTerminalInput] = useState('');
  const [terminalOutput, setTerminalOutput] = useState<{cmd: string, out: string}[]>([]);
  const [isTerminalOpen, setIsTerminalOpen] = useState(false);
  const [actionMessage, setActionMessage] = useState('');
  const [actionError, setActionError] = useState('');
  const [toolDiagnostics, setToolDiagnostics] = useState<ToolDiagnosticsReport | null>(null);
  const [isDiagnosticsLoading, setIsDiagnosticsLoading] = useState(false);
  const [lastDownloadStatus, setLastDownloadStatus] = useState<{
    phase: 'submitted' | 'active' | 'failed';
    message: string;
    url: string;
    updatedAt: number;
  } | null>(null);
  const [downloadTelemetry, setDownloadTelemetry] = useState<{
    clicks: number;
    lastFiredAt: number | null;
    lastOutcome: 'idle' | 'submitted' | 'failed' | 'blocked_no_url';
    lastUrlLength: number;
  }>({
    clicks: 0,
    lastFiredAt: null,
    lastOutcome: 'idle',
    lastUrlLength: 0,
  });
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('mega-get-theme');
      if (saved === 'light' || saved === 'dark') return saved;
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return 'dark';
  });
  
  const [notifiedTags, setNotifiedTags] = useState<Set<string>>(new Set());
  
  const logEndRef = useRef<HTMLDivElement>(null);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [terminalOutput]);
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
      new Notification(title, { body, icon: '/favicon.ico' });
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
      handleDownload(undefined, text);
    }
  };

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('mega-get-theme', theme);
  }, [theme]);

  useEffect(() => {
    fetchConfig();
    fetchHistory();
    fetchLogs();
    fetchAccount();
    fetchAnalytics();
    fetchToolDiagnostics();
    
    const interval = setInterval(() => {
      fetchTransfers();
      fetchLogs();
      fetchAccount();
      fetchAnalytics();
    }, 1000);
    const diagInterval = setInterval(() => {
      fetchToolDiagnostics();
    }, 15000);

    return () => {
      clearInterval(interval);
      clearInterval(diagInterval);
    };
  }, []);

  useEffect(() => {
    if (isLogExpanded) {
      scrollToBottom();
    }
  }, [logs, isLogExpanded]);

  const scrollToBottom = () => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchConfig = async () => {
    try {
      const res = await fetch('/api/config');
      const data = await res.json();
      setConfig(data);
      setTempPath(data.download_dir);
      setTempLimit(data.transfer_limit);
      setTempHistoryLimit(data.history_limit);
      setTempRetentionDays(data.history_retention_days);
      setTempMaxRetries(data.max_retries);
      setTempGlobalSpeedLimit(data.global_speed_limit_kbps);
      setTempScheduledStart(data.scheduled_start);
      setTempScheduledStop(data.scheduled_stop);
      setTempSchedulingEnabled(data.is_scheduling_enabled);
      setTempSoundAlertsEnabled(data.sound_alerts_enabled);
      setTempPrivacyMode(data.is_privacy_mode);
      setTempCompactMode(data.is_compact_mode);
      setTempPostAction(data.post_download_action);
      setTempWebhookUrl(data.webhook_url);
      setTempWatchEnabled(data.watch_folder_enabled);
      setTempWatchPath(data.watch_folder_path);
    } catch (err) {
      console.error('Failed to fetch config', err);
    }
  };

  const updateConfigInState = (raw: Record<string, unknown>) => {
    const data = mergeAppConfig(raw);
    setTempPath(data.download_dir);
    setTempLimit(data.transfer_limit);
    setTempHistoryLimit(data.history_limit);
    setTempRetentionDays(data.history_retention_days);
    setTempMaxRetries(data.max_retries);
    setTempGlobalSpeedLimit(data.global_speed_limit_kbps);
    setTempScheduledStart(data.scheduled_start);
    setTempScheduledStop(data.scheduled_stop);
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
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      if (res.ok) {
        const raw = await res.json();
        const data = mergeAppConfig(raw);
        setConfig((prev) => (prev ? { ...prev, ...data } : data));
        setIsEditingPath(false);
        setIsEditingLimit(false);
        setIsEditingHistoryLimit(false);
        setIsEditingRetention(false);
        updateConfigInState(raw);
      }
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

  const fetchAccount = async () => {
    try {
      const res = await fetch('/api/account');
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data = await res.json();
      setAccountInfo(data);
    } catch (err) {
      console.error('Failed to fetch account info', err);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await fetch('/api/analytics');
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        throw new Error("Not a JSON response");
      }
      const data = await res.json();
      setAnalytics(data);
    } catch (err) {
      console.error('Failed to fetch analytics', err);
    }
  };

  const fetchToolDiagnostics = async () => {
    try {
      setIsDiagnosticsLoading(true);
      const res = await fetch('/api/diag/tools');
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data: ToolDiagnosticsReport = await res.json();
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
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });
      const data = await res.json();
      if (data.status === 'success') {
        setAccountInfo(data.account);
        setIsLoginOpen(false);
        setLoginEmail('');
        setLoginPassword('');
        setActionMessage(data.message || 'Login successful.');
      } else {
        const msg = data?.message || `Login failed (${res.status})`;
        setActionError(msg);
        console.error('Login failed', msg);
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
      await fetch('/api/logout', { method: 'POST' });
      setAccountInfo(null);
      fetchAccount();
    } catch (err) {
      console.error('Logout failed', err);
    }
  };

  const executeCommand = async (cmd?: string) => {
    const commandToExecute = cmd || terminalInput;
    if (!commandToExecute.trim()) return;

    try {
      setActionError('');
      const res = await fetch('/api/terminal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: commandToExecute })
      });
      const data = await res.json();
      if (data.output === 'TERMINAL_CLEAR') {
        setTerminalOutput([]);
      } else {
        setTerminalOutput(prev => [...prev, { cmd: commandToExecute, out: data.output }]);
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

  const fetchTransfers = async () => {
    try {
      const res = await fetch('/api/transfers');
      const data: Transfer[] = await res.json();
      
      // Check for completions/failures to notify
      data.forEach(t => {
        if (!notifiedTags.has(t.tag)) {
          if (t.state === 'COMPLETED') {
            sendNotification('Download Completed', `Finished: ${t.filename}`);
            playAlert();
            setNotifiedTags(prev => new Set(prev).add(t.tag));
          } else if (t.state === 'FAILED') {
            sendNotification('Download Failed', `Error downloading: ${t.filename}`);
            setNotifiedTags(prev => new Set(prev).add(t.tag));
          }
        }
      });

      setTransfers(data);
    } catch (err) {
      console.error('Failed to fetch transfers', err);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch('/api/history');
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data = await res.json();
      setHistory(normalizeHistory(data));
    } catch (err) {
      console.error('Failed to fetch history', err);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch('/api/logs');
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data = await res.json();
      const normalized = normalizeLogs(data);
      setLogs(normalized);
      if (lastDownloadStatus && (lastDownloadStatus.phase === 'submitted' || lastDownloadStatus.phase === 'active')) {
        const messages = normalized.map((l) => l.message);
        const hasStarted = messages.some((m) => m.includes('✓ Download started successfully'));
        const failLine = [...messages].reverse().find((m) => m.includes('✗ Error'));
        const detailsLine = [...messages].reverse().find((m) => m.startsWith('Details:'));
        if (failLine) {
          setLastDownloadStatus((prev) =>
            prev
              ? {
                  ...prev,
                  phase: 'failed',
                  message: detailsLine || failLine,
                  updatedAt: Date.now(),
                }
              : prev
          );
        } else if (hasStarted && lastDownloadStatus.phase !== 'active') {
          setLastDownloadStatus((prev) =>
            prev
              ? {
                  ...prev,
                  phase: 'active',
                  message: 'Download started in MEGAcmd transfer queue.',
                  updatedAt: Date.now(),
                }
              : prev
          );
        }
      }
    } catch (err) {
      console.error('Failed to fetch logs', err);
    }
  };

  const handleDownload = async (e?: React.FormEvent, overrideUrl?: string, tags?: string[], priority?: TransferPriority) => {
    e?.preventDefault();
    console.log('handleDownload fired');
    const targetUrl = (overrideUrl || url || '').trim();
    setDownloadTelemetry((prev) => ({
      clicks: prev.clicks + 1,
      lastFiredAt: Date.now(),
      lastOutcome: prev.lastOutcome,
      lastUrlLength: targetUrl.length,
    }));
    if (!targetUrl) {
      setDownloadTelemetry((prev) => ({
        ...prev,
        lastOutcome: 'blocked_no_url',
      }));
      setActionError('No URL detected in the download field.');
      return;
    }

    setIsDownloadSubmitting(true);
    setActionError('');
    setActionMessage('');
    try {
      const res = await fetch('/api/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          url: targetUrl,
          tags: tags || [],
          priority: priority || 'NORMAL'
        }),
      });
      const data = await res.json();
      if (res.ok) {
        if (!overrideUrl) setUrl('');
        fetchTransfers();
        fetchHistory();
        setActionMessage(data?.message || 'Download submitted.');
        setDownloadTelemetry((prev) => ({
          ...prev,
          lastOutcome: 'submitted',
        }));
        setLastDownloadStatus({
          phase: 'submitted',
          message: data?.message || 'Download submitted to backend.',
          url: targetUrl,
          updatedAt: Date.now(),
        });
      } else {
        const msg = data?.detail || data?.message || `Download failed (${res.status})`;
        setActionError(msg);
        setDownloadTelemetry((prev) => ({
          ...prev,
          lastOutcome: 'failed',
        }));
        setLastDownloadStatus({
          phase: 'failed',
          message: msg,
          url: targetUrl,
          updatedAt: Date.now(),
        });
      }
    } catch (err) {
      setActionError('Download request failed. Check API/MEGAcmd status.');
      setDownloadTelemetry((prev) => ({
        ...prev,
        lastOutcome: 'failed',
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
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      console.error('Copy to clipboard failed', err);
    }
  };

  const handleInstallCommand = async (cmd: string) => {
    await copyToClipboard(cmd);
    setActionMessage('Install command copied. Paste and run it in your system terminal.');
    setActionError('');
  };

  const handleAction = async (tag: string, action: 'pause' | 'resume' | 'cancel' | 'retry') => {
    try {
      await fetch(`/api/transfers/${tag}/${action}`, { method: 'POST' });
      fetchTransfers();
      if (action === 'cancel') {
        setSelectedTransfers(prev => {
          const next = new Set(prev);
          next.delete(tag);
          return next;
        });
      }
    } catch (err) {
      console.error(`Failed to ${action} transfer ${tag}`, err);
    }
  };

  const handleSetSpeedLimit = async (tag: string, limitKbps: number) => {
    try {
      setActionError('');
      const res = await fetch(`/api/transfers/${tag}/limit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speed_limit_kbps: limitKbps }),
      });
      const data = await res.json();
      if (!res.ok) {
        setActionError(data?.detail || `Failed to set speed limit (${res.status})`);
        return;
      }
      setActionMessage(data?.message || 'Speed limit updated.');
      if (data?.applied_to_megacmd === false) {
        setActionError('Speed limit saved as UI policy only (not directly enforced by MEGAcmd).');
      }
      fetchTransfers();
    } catch (err) {
      setActionError(`Failed to set speed limit for ${tag}.`);
      console.error(`Failed to set speed limit for ${tag}`, err);
    }
  };

  const toggleSelect = (tag: string) => {
    setSelectedTransfers(prev => {
      const next = new Set(prev);
      if (next.has(tag)) next.delete(tag);
      else next.add(tag);
      return next;
    });
  };

  const selectAll = (section: 'active' | 'completed') => {
    const items = section === 'active' ? sortedTransfers : completedTransfers;
    const allSelected = items.every(t => selectedTransfers.has(t.tag));
    
    setSelectedTransfers(prev => {
      const next = new Set(prev);
      if (allSelected) {
        items.forEach(t => next.delete(t.tag));
      } else {
        items.forEach(t => next.add(t.tag));
      }
      return next;
    });
  };

  const handleBulkAction = async (action: string, value?: any) => {
    const tags = Array.from(selectedTransfers);
    if (tags.length === 0) return;

    setIsLoading(true);
    setActionError('');
    setActionMessage('');
    try {
      if (action === 'redownload') {
        const selectedItems = transfers.filter(t => selectedTransfers.has(t.tag));
        for (const t of selectedItems) {
          await handleDownload(undefined, t.url, t.tags, t.priority);
        }
      } else {
        const res = await fetch('/api/transfers/bulk', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tags, action, value }),
        });
        if (res.ok) {
          const data = await res.json();
          setActionMessage(`Bulk action "${action}" applied to ${data?.affectedCount ?? 0} transfer(s).`);
          if (action === 'remove' || action === 'cancel') {
            setSelectedTransfers(new Set());
          }
        } else {
          const data = await res.json();
          setActionError(data?.detail || `Bulk action failed (${res.status})`);
        }
      }
      
      fetchTransfers();
      fetchHistory();
    } catch (err) {
      setActionError(`Bulk action ${action} failed.`);
      console.error(`Bulk action ${action} failed`, err);
    } finally {
      setTimeout(() => setIsLoading(false), 500);
    }
  };

  const handleCancelAll = async () => {
    try {
      await fetch('/api/transfers/cancel-all', { method: 'POST' });
      fetchTransfers();
    } catch (err) {
      console.error('Failed to cancel all transfers', err);
    }
  };

  const clearHistory = async () => {
    try {
      await fetch('/api/history', { method: 'DELETE' });
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
      const res = await fetch('/api/logs', { method: 'DELETE' });
      const data = await res.json();
      if (!res.ok) {
        setActionError(data?.detail || `Failed to clear logs (${res.status})`);
        return;
      }
      await fetchLogs();
      setActionMessage('Logs cleared on server.');
    } catch (err) {
      setActionError('Failed to clear logs.');
      console.error('Failed to clear logs', err);
    }
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case 'ACTIVE': return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
      case 'QUEUED': return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
      case 'PAUSED': return 'text-gray-400 bg-gray-400/10 border-gray-400/20';
      case 'RETRYING': return 'text-orange-400 bg-orange-400/10 border-orange-400/20';
      case 'COMPLETED': return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
      case 'FAILED': return 'text-rose-400 bg-rose-400/10 border-rose-400/20';
      default: return 'text-gray-400 bg-gray-400/10 border-gray-400/20';
    }
  };

  const getStateIcon = (state: string) => {
    switch (state) {
      case 'ACTIVE': return <RefreshCw className="w-3 h-3 animate-spin" />;
      case 'QUEUED': return <Clock className="w-3 h-3" />;
      case 'PAUSED': return <Pause className="w-3 h-3" />;
      case 'RETRYING': return <RefreshCw className="w-3 h-3" />;
      case 'COMPLETED': return <CheckCircle2 className="w-3 h-3" />;
      case 'FAILED': return <AlertCircle className="w-3 h-3" />;
      default: return null;
    }
  };

  const formatBytes = (bytes: number, decimals = 2) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  const formatSpeed = (bps: number) => {
    return `${formatBytes(bps)}/s`;
  };

  const formatETA = (seconds: number) => {
    if (!isFinite(seconds) || seconds < 0) return '--';
    if (seconds === 0) return '0s';

    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);

    const parts = [];
    if (h > 0) parts.push(`${h}h`);
    if (m > 0) parts.push(`${m}m`);
    if (s > 0 || parts.length === 0) parts.push(`${s}s`);

    return parts.join(' ');
  };

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  const filteredTransfers = transfers.filter(t => {
    const q = (searchQuery || '').toLowerCase();
    const matchesSearch = (t.filename || '').toLowerCase().includes(q) || 
      (t.tag || '').includes(searchQuery || '') ||
      (t.url || '').toLowerCase().includes(q);
    
    const matchesState = filterState === 'ALL' || t.state === filterState;
    const matchesPriority = filterPriority === 'ALL' || t.priority === filterPriority;
    const matchesLabel = filterLabel === 'ALL' || (t.tags && t.tags.includes(filterLabel));

    return matchesSearch && matchesState && matchesPriority && matchesLabel;
  });

  const filteredHistory = history.filter(h => 
    (h.url || '').toLowerCase().includes((historySearchQuery || '').toLowerCase())
  );

  const filteredLogs = logs.filter(log => {
    const q = (logSearchQuery || '').toLowerCase();
    const matchesSearch = (log.message || '').toLowerCase().includes(q) || 
      (log.tag && log.tag.includes(logSearchQuery || ''));
    const matchesLevel = logFilterLevel === 'ALL' || log.level === logFilterLevel;
    const matchesCategory = logFilterCategory === 'ALL' || log.category === logFilterCategory;
    return matchesSearch && matchesLevel && matchesCategory;
  });

  const sortedTransfers = [...filteredTransfers]
    .filter(t => t.state !== 'COMPLETED')
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

  const completedTransfers = filteredTransfers.filter(t => t.state === 'COMPLETED');

  return (
    <div 
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className="min-h-screen bg-[var(--background)] text-[var(--foreground)] font-sans selection:bg-blue-500/30 transition-colors duration-300 relative"
    >
      <AnimatePresence>
        {isDragging && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] bg-blue-600/20 backdrop-blur-md flex items-center justify-center border-4 border-dashed border-blue-500 m-4 rounded-3xl pointer-events-none"
          >
            <div className="bg-[var(--card)] p-8 rounded-2xl shadow-2xl flex flex-col items-center gap-4">
              <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center animate-bounce">
                <Plus className="text-white w-8 h-8" />
              </div>
              <p className="text-xl font-bold">Drop MEGA Link to Download</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--card)]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-400 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
              <CloudDownload className="text-white w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-[var(--foreground)]">LinkTugger</h1>
              <div className="flex items-center gap-2">
                <p className="text-[10px] uppercase tracking-widest text-[var(--muted-foreground)] font-semibold">Cloud Download Manager</p>
                {config?.is_scheduling_enabled && (
                  <div className="flex items-center gap-1 px-1.5 py-0.5 bg-amber-500/10 border border-amber-500/20 rounded text-[9px] font-bold text-amber-500 uppercase animate-pulse">
                    <Timer className="w-2.5 h-2.5" />
                    Scheduled
                  </div>
                )}
                {config?.watch_folder_enabled && (
                  <div className="flex items-center gap-1 px-1.5 py-0.5 bg-emerald-500/10 border border-emerald-500/20 rounded text-[9px] font-bold text-emerald-500 uppercase">
                    <Activity className="w-2.5 h-2.5" />
                    Watch Folder
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-6">
            <button 
              onClick={() => setActiveTab('transfers')}
              className={`text-sm font-bold transition-all relative py-2 ${activeTab === 'transfers' ? 'text-blue-500' : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'}`}
            >
              Transfers
              {activeTab === 'transfers' && <motion.div layoutId="tab-underline" className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 rounded-full" />}
            </button>
            <button 
              onClick={() => setActiveTab('history')}
              className={`text-sm font-bold transition-all relative py-2 ${activeTab === 'history' ? 'text-blue-500' : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'}`}
            >
              History
              {activeTab === 'history' && <motion.div layoutId="tab-underline" className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 rounded-full" />}
            </button>
            <button 
              onClick={() => setActiveTab('analytics')}
              className={`text-sm font-bold transition-all relative py-2 ${activeTab === 'analytics' ? 'text-blue-500' : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'}`}
            >
              Analytics
              {activeTab === 'analytics' && <motion.div layoutId="tab-underline" className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 rounded-full" />}
            </button>
          </div>
          
          <div className="flex items-center gap-4">
            {accountInfo?.is_logged_in ? (
              <div className="flex items-center gap-6">
                {/* Bandwidth Quota */}
                <div className="hidden lg:flex flex-col items-end gap-1">
                  <div className="flex items-center gap-2 text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-wider">
                    <ArrowUpDown className="w-3 h-3 text-blue-500" />
                    Bandwidth Quota
                  </div>
                  {accountInfo.bandwidth_limit_bytes > 0 ? (
                    <>
                      <div className="w-32 h-1.5 bg-[var(--muted)] rounded-full overflow-hidden border border-[var(--border)]">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${quotaBarWidthPct(accountInfo.bandwidth_used_bytes, accountInfo.bandwidth_limit_bytes)}%` }}
                          className="h-full bg-blue-500"
                        />
                      </div>
                      <span className="text-[9px] text-[var(--muted-foreground)]/60 font-mono">
                        {formatBytes(accountInfo.bandwidth_used_bytes)} / {formatBytes(accountInfo.bandwidth_limit_bytes)}
                      </span>
                    </>
                  ) : (
                    <span className="text-[9px] text-[var(--muted-foreground)]/60 font-mono max-w-[10rem] text-right">
                      {formatBytes(accountInfo.bandwidth_used_bytes)} used (quota not reported)
                    </span>
                  )}
                </div>

                {/* Account Info */}
                <div className="flex items-center gap-3 bg-[var(--muted)]/50 border border-[var(--border)] px-3 py-1.5 rounded-2xl">
                  <div className="flex flex-col items-end">
                    <span className={`text-xs font-bold text-[var(--foreground)] truncate max-w-[120px] ${config?.is_privacy_mode ? 'blur-sm select-none' : ''}`}>
                      {accountInfo.email}
                    </span>
                    <span className="text-[9px] font-bold text-blue-500 uppercase tracking-widest flex items-center gap-1">
                      <ShieldCheck className="w-2.5 h-2.5" />
                      {accountTypeLabel(accountInfo.account_type)} Account
                    </span>
                  </div>
                  <button 
                    onClick={handleLogout}
                    className="p-1.5 hover:bg-rose-500/10 rounded-lg text-[var(--muted-foreground)] hover:text-rose-500 transition-colors"
                    title="Logout"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ) : (
              <button 
                onClick={() => setIsLoginOpen(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-blue-500/20 active:scale-95"
              >
                <LogIn className="w-4 h-4" />
                Login to MEGA
              </button>
            )}

            {config && (
              <div className="hidden md:flex flex-col items-end text-xs text-[var(--muted-foreground)]">
                <span className="text-[10px] uppercase text-[var(--muted-foreground)]/60 font-bold">Download Path</span>
                {isEditingPath ? (
                  <div className="flex items-center gap-2 mt-1">
                    <input
                      type="text"
                      value={tempPath}
                      onChange={(e) => setTempPath(e.target.value)}
                      className="bg-[var(--muted)] border border-[var(--border)] rounded px-2 py-0.5 text-[11px] font-mono focus:outline-none focus:ring-1 focus:ring-blue-500/50 w-48"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') updateConfig({ download_dir: tempPath });
                        if (e.key === 'Escape') {
                          setIsEditingPath(false);
                          setTempPath(config.download_dir);
                        }
                      }}
                    />
                    <button onClick={() => updateConfig({ download_dir: tempPath })} className="text-blue-500 hover:text-blue-400 font-bold">Save</button>
                    <button onClick={() => { setIsEditingPath(false); setTempPath(config.download_dir); }} className="text-rose-500 hover:text-rose-400 font-bold">Cancel</button>
                  </div>
                ) : (
                  <button 
                    onClick={() => setIsEditingPath(true)}
                    className="font-mono hover:text-blue-500 transition-colors flex items-center gap-1.5 group"
                  >
                    {config.download_dir}
                    <Plus className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity rotate-45" />
                  </button>
                )}
              </div>
            )}

            {config && (
              <div className="hidden md:flex flex-col items-end text-xs text-[var(--muted-foreground)]">
                <span className="text-[10px] uppercase text-[var(--muted-foreground)]/60 font-bold">Concurrent Limit</span>
                {isEditingLimit ? (
                  <div className="flex items-center gap-2 mt-1">
                    <input
                      type="number"
                      value={tempLimit}
                      onChange={(e) => setTempLimit(parseInt(e.target.value) || 1)}
                      min="1"
                      className="bg-[var(--muted)] border border-[var(--border)] rounded px-2 py-0.5 text-[11px] font-mono focus:outline-none focus:ring-1 focus:ring-blue-500/50 w-16"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') updateConfig({ transfer_limit: tempLimit });
                        if (e.key === 'Escape') {
                          setIsEditingLimit(false);
                          setTempLimit(config.transfer_limit);
                        }
                      }}
                    />
                    <button onClick={() => updateConfig({ transfer_limit: tempLimit })} className="text-blue-500 hover:text-blue-400 font-bold">Save</button>
                  </div>
                ) : (
                  <button 
                    onClick={() => setIsEditingLimit(true)}
                    className="font-mono hover:text-blue-500 transition-colors flex items-center gap-1.5 group"
                  >
                    {config.transfer_limit} Slots
                    <Plus className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity rotate-45" />
                  </button>
                )}
              </div>
            )}

            {config && (
              <div className="hidden lg:flex flex-col items-end text-xs text-[var(--muted-foreground)] border-l border-[var(--border)] pl-4">
                <span className="text-[10px] uppercase text-[var(--muted-foreground)]/60 font-bold">History Limit</span>
                {isEditingHistoryLimit ? (
                  <div className="flex items-center gap-2 mt-1">
                    <input
                      type="number"
                      value={tempHistoryLimit}
                      onChange={(e) => setTempHistoryLimit(parseInt(e.target.value) || 0)}
                      min="0"
                      className="bg-[var(--muted)] border border-[var(--border)] rounded px-2 py-0.5 text-[11px] font-mono focus:outline-none focus:ring-1 focus:ring-blue-500/50 w-16"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') updateConfig({ history_limit: tempHistoryLimit });
                        if (e.key === 'Escape') {
                          setIsEditingHistoryLimit(false);
                          setTempHistoryLimit(config.history_limit);
                        }
                      }}
                    />
                    <button onClick={() => updateConfig({ history_limit: tempHistoryLimit })} className="text-blue-500 hover:text-blue-400 font-bold">Save</button>
                  </div>
                ) : (
                  <button 
                    onClick={() => setIsEditingHistoryLimit(true)}
                    className="font-mono hover:text-blue-500 transition-colors flex items-center gap-1.5 group"
                  >
                    {config.history_limit} Items
                    <Plus className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity rotate-45" />
                  </button>
                )}
              </div>
            )}

            {config && (
              <div className="hidden lg:flex flex-col items-end text-xs text-[var(--muted-foreground)] border-l border-[var(--border)] pl-4">
                <span className="text-[10px] uppercase text-[var(--muted-foreground)]/60 font-bold">Retention</span>
                {isEditingRetention ? (
                  <div className="flex items-center gap-2 mt-1">
                    <input
                      type="number"
                      value={tempRetentionDays}
                      onChange={(e) => setTempRetentionDays(parseInt(e.target.value) || 0)}
                      min="0"
                      className="bg-[var(--muted)] border border-[var(--border)] rounded px-2 py-0.5 text-[11px] font-mono focus:outline-none focus:ring-1 focus:ring-blue-500/50 w-16"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') updateConfig({ history_retention_days: tempRetentionDays });
                        if (e.key === 'Escape') {
                          setIsEditingRetention(false);
                          setTempRetentionDays(config.history_retention_days);
                        }
                      }}
                    />
                    <button onClick={() => updateConfig({ history_retention_days: tempRetentionDays })} className="text-blue-500 hover:text-blue-400 font-bold">Save</button>
                  </div>
                ) : (
                  <button 
                    onClick={() => setIsEditingRetention(true)}
                    className="font-mono hover:text-blue-500 transition-colors flex items-center gap-1.5 group"
                  >
                    {config.history_retention_days} Days
                    <Plus className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity rotate-45" />
                  </button>
                )}
              </div>
            )}
            
            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl bg-[var(--muted)] hover:bg-[var(--border)] text-[var(--foreground)] transition-colors border border-[var(--border)]"
              title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            >
              {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            </button>

            <button
              onClick={() => setIsSettingsOpen(true)}
              className="p-2 rounded-xl bg-[var(--muted)] hover:bg-[var(--border)] text-[var(--foreground)] transition-colors border border-[var(--border)]"
              title="Advanced Settings"
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
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

        {toolDiagnostics && (
          <div className="mb-4 rounded-2xl border border-[var(--border)] bg-[var(--card)] p-4">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Command className="h-4 w-4 text-amber-500" />
                <span className="text-sm font-bold">Tool Diagnostics</span>
                {!toolDiagnostics.ok && (
                  <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-amber-500">
                    {toolDiagnostics.missing_tools.length} missing
                  </span>
                )}
              </div>
              <button
                onClick={fetchToolDiagnostics}
                className="rounded-lg border border-[var(--border)] px-2 py-1 text-[11px] font-bold hover:bg-[var(--muted)]"
              >
                Refresh
              </button>
            </div>

            {isDiagnosticsLoading && (
              <p className="mb-2 text-xs text-[var(--muted-foreground)]">Refreshing diagnostics...</p>
            )}

            <div className="space-y-3">
              {toolDiagnostics.tools.map((tool) => (
                  <div key={tool.name} className="rounded-xl border border-[var(--border)] bg-[var(--muted)]/30 p-3">
                    <div className="mb-1 flex items-center gap-2">
                      {tool.available ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-rose-500" />
                      )}
                      <span className="text-sm font-bold">{tool.name}</span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${
                          tool.available
                            ? 'border border-emerald-500/30 bg-emerald-500/10 text-emerald-500'
                            : 'border border-rose-500/30 bg-rose-500/10 text-rose-500'
                        }`}
                      >
                        {tool.available ? 'available' : 'missing'}
                      </span>
                    </div>
                    {!!tool.required_for?.length && (
                      <p className="text-xs text-[var(--muted-foreground)]">
                        Required for: {tool.required_for.join(', ')}
                      </p>
                    )}
                    {!!tool.install_instructions && (
                      <p className="mt-1 text-xs text-[var(--muted-foreground)]">{tool.install_instructions}</p>
                    )}
                    {!tool.available && !!tool.suggested_install_commands?.length && (
                      <div className="mt-2 space-y-2">
                        {tool.suggested_install_commands.map((cmd) => (
                          <div key={`${tool.name}-${cmd}`} className="rounded-lg border border-[var(--border)] bg-[var(--background)] p-2">
                            <code className="block overflow-x-auto text-[11px]">{cmd}</code>
                            <div className="mt-2 flex items-center gap-2">
                              <button
                                onClick={() => handleInstallCommand(cmd)}
                                className="rounded-md bg-blue-600 px-2 py-1 text-[10px] font-bold text-white hover:bg-blue-500"
                              >
                                Install
                              </button>
                              <button
                                onClick={() => copyToClipboard(cmd)}
                                className="rounded-md border border-[var(--border)] px-2 py-1 text-[10px] font-bold hover:bg-[var(--muted)]"
                              >
                                Copy command
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
            </div>
          </div>
        )}
        {/* Add Download Section */}
        <section className="mb-12">
          <div className="bg-gradient-to-b from-blue-500/10 to-transparent p-[1px] rounded-2xl">
            <div className="bg-[var(--card)] rounded-2xl p-6 shadow-xl border border-[var(--border)]">
              {lastDownloadStatus && (
                <div
                  className={`mb-4 rounded-xl border px-3 py-2 text-xs ${
                    lastDownloadStatus.phase === 'failed'
                      ? 'border-rose-500/40 text-rose-400 bg-rose-500/10'
                      : lastDownloadStatus.phase === 'active'
                      ? 'border-emerald-500/40 text-emerald-400 bg-emerald-500/10'
                      : 'border-amber-500/40 text-amber-400 bg-amber-500/10'
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-semibold uppercase tracking-wide">
                      Last download: {lastDownloadStatus.phase}
                    </div>
                    {lastDownloadStatus.phase === 'failed' && (
                      <button
                        type="button"
                        onClick={() => handleDownload(undefined, lastDownloadStatus.url)}
                        className="rounded-md border border-current/30 px-2 py-1 text-[10px] font-bold uppercase hover:bg-white/10"
                      >
                        Retry
                      </button>
                    )}
                  </div>
                  <div className="mt-1">{lastDownloadStatus.message}</div>
                </div>
              )}
              <div className="mb-3 rounded-lg border border-[var(--border)] bg-[var(--background)]/60 px-3 py-2 text-[11px] text-[var(--muted-foreground)]">
                <span className="font-semibold">Download telemetry (temp): </span>
                clicks={downloadTelemetry.clicks} ·
                fired_at={downloadTelemetry.lastFiredAt ? new Date(downloadTelemetry.lastFiredAt).toLocaleTimeString() : 'never'} ·
                outcome={downloadTelemetry.lastOutcome} ·
                url_len={downloadTelemetry.lastUrlLength}
              </div>
              <form 
                onSubmit={(e) => {
                  e.preventDefault();
                  handleDownload(e, undefined, newDownloadTags.split(',').map(t => t.trim()).filter(t => t), newDownloadPriority);
                  setNewDownloadTags('');
                  setNewDownloadPriority('NORMAL');
                }} 
                className="flex flex-col gap-4"
              >
                <div className="flex flex-col md:flex-row gap-4">
                  <div className="relative flex-[2]">
                    <input
                      type="text"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="Paste MEGA.nz export link here..."
                      className="w-full bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-3.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all placeholder:text-[var(--muted-foreground)] text-[var(--foreground)]"
                    />
                  </div>
                  <div className="relative flex-1">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search transfers..."
                      className="w-full bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-3.5 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all placeholder:text-[var(--muted-foreground)] text-[var(--foreground)]"
                    />
                    {searchQuery && (
                      <button 
                        onClick={() => setSearchQuery('')}
                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-[var(--muted)] rounded-full text-[var(--muted-foreground)] transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
                <div className="flex flex-col md:flex-row gap-4 items-center">
                  <div className="flex-1 flex items-center gap-2 bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-2">
                    <Tag className="w-4 h-4 text-[var(--muted-foreground)]" />
                    <input
                      type="text"
                      value={newDownloadTags}
                      onChange={(e) => setNewDownloadTags(e.target.value)}
                      placeholder="Tags (comma separated)..."
                      className="flex-1 bg-transparent text-sm focus:outline-none placeholder:text-[var(--muted-foreground)]/60"
                    />
                  </div>
                  <div className="flex items-center gap-2 bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-2">
                    <span className="text-xs font-bold text-[var(--muted-foreground)] uppercase">Priority:</span>
                    <select
                      value={newDownloadPriority}
                      onChange={(e) => setNewDownloadPriority(e.target.value as TransferPriority)}
                      className="bg-transparent text-sm font-bold focus:outline-none cursor-pointer"
                    >
                      <option value="LOW">Low</option>
                      <option value="NORMAL">Normal</option>
                      <option value="HIGH">High</option>
                    </select>
                  </div>
                  <button
                    type="submit"
                    disabled={isDownloadSubmitting || !url.trim()}
                    className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:hover:bg-blue-600 text-white font-semibold px-8 py-3 rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-blue-600/20 active:scale-95 ml-auto"
                  >
                    {isDownloadSubmitting ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Plus className="w-5 h-5" />}
                    Download
                  </button>
                </div>
              </form>
            </div>
          </div>
        </section>

        <div className="grid grid-cols-1 gap-8">
          {activeTab === 'transfers' && (
            <div className="space-y-6">
              {/* Active Transfers */}
              <div className="flex flex-col gap-4 mb-6">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <button 
                    onClick={() => selectAll('active')}
                    className="p-1 hover:bg-[var(--muted)] rounded transition-colors text-[var(--muted-foreground)]"
                    title="Select All Active"
                  >
                    {sortedTransfers.length > 0 && sortedTransfers.every(t => selectedTransfers.has(t.tag)) ? (
                      <CheckSquare className="w-5 h-5 text-blue-500" />
                    ) : (
                      <Square className="w-5 h-5" />
                    )}
                  </button>
                  Active Transfers
                  <span className="bg-white/5 text-gray-400 text-[10px] px-2 py-0.5 rounded-full border border-white/10">
                    {transfers.length}
                  </span>
                </h2>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2 bg-[var(--muted)] p-1 rounded-lg border border-[var(--border)]">
                    <Filter className="w-3 h-3 ml-2 text-[var(--muted-foreground)]" />
                    <select 
                      value={filterState}
                      onChange={(e) => setFilterState(e.target.value as any)}
                      className="bg-transparent text-[10px] uppercase font-bold text-[var(--muted-foreground)] focus:outline-none px-2 cursor-pointer border-r border-[var(--border)]"
                    >
                      <option value="ALL">All States</option>
                      <option value="ACTIVE">Active</option>
                      <option value="QUEUED">Queued</option>
                      <option value="PAUSED">Paused</option>
                      <option value="FAILED">Failed</option>
                    </select>
                    <select 
                      value={filterPriority}
                      onChange={(e) => setFilterPriority(e.target.value as any)}
                      className="bg-transparent text-[10px] uppercase font-bold text-[var(--muted-foreground)] focus:outline-none px-2 cursor-pointer border-r border-[var(--border)]"
                    >
                      <option value="ALL">All Priorities</option>
                      <option value="HIGH">High</option>
                      <option value="NORMAL">Normal</option>
                      <option value="LOW">Low</option>
                    </select>
                    <div className="flex items-center gap-2 px-2">
                      <Tag className="w-3 h-3 text-[var(--muted-foreground)]" />
                      <input 
                        type="text"
                        value={filterLabel === 'ALL' ? '' : filterLabel}
                        onChange={(e) => setFilterLabel(e.target.value || 'ALL')}
                        placeholder="Filter Tag..."
                        className="bg-transparent text-[10px] uppercase font-bold text-[var(--muted-foreground)] focus:outline-none w-20 placeholder:text-[var(--muted-foreground)]/40"
                      />
                    </div>
                  </div>
                  <div className="flex items-center gap-2 bg-[var(--muted)] p-1 rounded-lg border border-[var(--border)]">
                    <select 
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value as any)}
                      className="bg-transparent text-[10px] uppercase font-bold text-[var(--muted-foreground)] focus:outline-none px-2 cursor-pointer"
                    >
                      <option value="filename">Name</option>
                      <option value="progress">Progress</option>
                      <option value="state">State</option>
                    </select>
                    <button 
                      onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
                      className="p-1 hover:bg-[var(--border)] rounded transition-colors text-[var(--muted-foreground)]"
                      title={`Sort ${sortOrder === 'asc' ? 'Descending' : 'Ascending'}`}
                    >
                      {sortOrder === 'asc' ? <SortAsc className="w-3 h-3" /> : <SortDesc className="w-3 h-3" />}
                    </button>
                  </div>
                </div>
              </div>

              {/* Bulk Action Bar */}
              <AnimatePresence>
                {selectedTransfers.size > 0 && (
                  <motion.div 
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="bg-blue-600/10 border border-blue-500/30 rounded-xl p-3 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-bold text-blue-500 px-2 py-1 bg-blue-500/10 rounded-lg">
                          {selectedTransfers.size} Selected
                        </span>
                        <div className="h-4 w-[1px] bg-blue-500/20 mx-2" />
                        <div className="flex items-center gap-1">
                          <button 
                            onClick={() => handleBulkAction('pause')}
                            className="p-2 hover:bg-blue-500/20 rounded-lg text-blue-500 transition-colors"
                            title="Pause Selected"
                          >
                            <Pause className="w-4 h-4" />
                          </button>
                          <button 
                            onClick={() => handleBulkAction('resume')}
                            className="p-2 hover:bg-blue-500/20 rounded-lg text-blue-500 transition-colors"
                            title="Resume Selected"
                          >
                            <Play className="w-4 h-4" />
                          </button>
                          <button 
                            onClick={() => handleBulkAction('cancel')}
                            className="p-2 hover:bg-rose-500/20 rounded-lg text-rose-500 transition-colors"
                            title="Cancel Selected"
                          >
                            <X className="w-4 h-4" />
                          </button>
                          <button 
                            onClick={() => handleBulkAction('redownload')}
                            className="p-2 hover:bg-blue-500/20 rounded-lg text-blue-500 transition-colors"
                            title="Redownload Selected"
                          >
                            <RefreshCw className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold text-[var(--muted-foreground)] uppercase">Priority:</span>
                          <div className="flex bg-[var(--muted)] p-0.5 rounded-lg border border-[var(--border)]">
                            {['LOW', 'NORMAL', 'HIGH'].map((p) => (
                              <button
                                key={p}
                                onClick={() => handleBulkAction('set_priority', p)}
                                className="px-2 py-1 text-[9px] font-bold rounded-md hover:bg-[var(--border)] transition-colors"
                              >
                                {p}
                              </button>
                            ))}
                          </div>
                        </div>
                        <button 
                          onClick={() => setSelectedTransfers(new Set())}
                          className="text-[10px] font-bold text-[var(--muted-foreground)] hover:text-[var(--foreground)] uppercase"
                        >
                          Deselect All
                        </button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="space-y-4">
              <AnimatePresence mode="popLayout">
                {sortedTransfers.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="bg-[var(--card)] border border-dashed border-[var(--border)] rounded-2xl py-20 flex flex-col items-center justify-center text-[var(--muted-foreground)]"
                  >
                    <CloudDownload className="w-12 h-12 mb-4 opacity-20" />
                    <p className="text-sm">No active transfers</p>
                    <p className="text-xs opacity-60">Paste a URL above to start downloading</p>
                  </motion.div>
                ) : (
                  sortedTransfers.map((t) => (
                    <motion.div
                      key={t.tag}
                      layout
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      className={`bg-[var(--card)] border rounded-2xl transition-all group shadow-sm flex gap-4 ${config?.is_compact_mode ? 'p-3 gap-3' : 'p-5 gap-4'} ${selectedTransfers.has(t.tag) ? 'border-blue-500 ring-1 ring-blue-500/20' : 'border-[var(--border)] hover:border-blue-500/30'}`}
                    >
                      <div className={config?.is_compact_mode ? 'pt-0.5' : 'pt-1'}>
                        <button 
                          onClick={() => toggleSelect(t.tag)}
                          className="p-1 hover:bg-[var(--muted)] rounded transition-colors text-[var(--muted-foreground)]"
                        >
                          {selectedTransfers.has(t.tag) ? (
                            <CheckSquare className="w-5 h-5 text-blue-500" />
                          ) : (
                            <Square className="w-5 h-5" />
                          )}
                        </button>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className={`flex items-start justify-between gap-4 ${config?.is_compact_mode ? 'mb-2' : 'mb-4'}`}>
                          <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 group/title">
                            <h3 className={`font-medium text-[var(--foreground)] truncate mb-1 ${config?.is_compact_mode ? 'text-xs' : 'text-sm'} ${config?.is_privacy_mode ? 'blur-md select-none' : ''}`} title={t.filename}>
                              {t.filename}
                            </h3>
                            <button 
                              onClick={() => copyToClipboard(t.filename)}
                              className="opacity-0 group-hover/title:opacity-100 p-1 hover:bg-[var(--muted)] rounded transition-opacity"
                              title="Copy filename"
                            >
                              <Copy className="w-3 h-3 text-[var(--muted-foreground)]" />
                            </button>
                          </div>
                            <div className={`flex items-center gap-3 text-[var(--muted-foreground)] ${config?.is_compact_mode ? 'text-[9px]' : 'text-[11px]'}`}>
                              <span className="font-mono bg-[var(--muted)] px-1.5 py-0.5 rounded border border-[var(--border)]">#{t.tag}</span>
                              <span className={`truncate max-w-[200px] ${config?.is_privacy_mode ? 'blur-sm select-none' : ''}`}>{t.path}</span>
                              {t.priority && t.priority !== 'NORMAL' && (
                                <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold uppercase ${t.priority === 'HIGH' ? 'bg-rose-500/10 text-rose-500 border border-rose-500/20' : 'bg-amber-500/10 text-amber-500 border border-amber-500/20'}`}>
                                  {t.priority}
                                </span>
                              )}
                              {t.tags && t.tags.length > 0 && (
                                <div className="flex items-center gap-1">
                                  {t.tags.map(tag => (
                                    <span key={tag} className="px-1.5 py-0.5 bg-blue-500/10 text-blue-500 border border-blue-500/20 rounded text-[8px] font-bold uppercase">
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                          <div className={`flex items-center gap-1.5 rounded-full border font-bold uppercase tracking-wider ${config?.is_compact_mode ? 'px-2 py-0.5 text-[8px]' : 'px-2.5 py-1 text-[10px]'} ${getStateColor(t.state)}`}>
                            {getStateIcon(t.state)}
                            {t.state}
                          </div>
                        </div>

                        <div className="space-y-3">
                          <div className="flex items-center justify-between text-xs mb-1">
                            <div className="flex flex-col gap-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                {t.size_bytes === 0 ? (
                                  <>
                                    <span className="font-semibold text-[var(--foreground)]">{t.progress_pct}%</span>
                                    <span className="text-[var(--muted-foreground)]">Unknown size</span>
                                  </>
                                ) : (
                                  <>
                                    <span className="font-semibold text-[var(--foreground)]">
                                      {formatBytes(t.downloaded_bytes)}
                                    </span>
                                    <span className="text-[var(--muted-foreground)]">of {formatBytes(t.size_bytes)}</span>
                                    <span className="text-blue-500 font-bold ml-1">({t.progress_pct}%)</span>
                                  </>
                                )}
                              </div>
                              {t.state === 'ACTIVE' && t.speed_bps > 0 && (
                                <div className="flex items-center gap-3 text-[10px] text-[var(--muted-foreground)] font-medium">
                                  <span className="flex items-center gap-1">
                                    <RefreshCw className="w-2.5 h-2.5" />
                                    {formatSpeed(t.speed_bps)}
                                  </span>
                                  {t.size_bytes > 0 && (
                                  <span className="flex items-center gap-1">
                                    <Clock className="w-2.5 h-2.5" />
                                    ETA: {formatETA((t.size_bytes - t.downloaded_bytes) / t.speed_bps)}
                                  </span>
                                  )}
                                  <div className="flex items-center gap-1 ml-2 bg-[var(--muted)] px-1.5 py-0.5 rounded border border-[var(--border)] group/limit">
                                    <Gauge className="w-2.5 h-2.5 text-blue-500" />
                                    <input
                                      type="number"
                                      defaultValue={t.speed_limit_kbps || 0}
                                      onBlur={(e) => handleSetSpeedLimit(t.tag, parseInt(e.target.value) || 0)}
                                      className="w-12 bg-transparent focus:outline-none text-[9px] font-bold"
                                      title="Set Speed Limit (KB/s)"
                                    />
                                    <span className="text-[8px] uppercase opacity-40">KB/s</span>
                                  </div>
                                </div>
                              )}
                            </div>
                            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              {(t.state === 'FAILED' || t.state === 'RETRYING') && (
                                <button 
                                  onClick={() => handleAction(t.tag, 'retry')}
                                  className="p-1.5 hover:bg-[var(--muted)] rounded-lg text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
                                  title="Retry"
                                >
                                  <RotateCcw className="w-4 h-4" />
                                </button>
                              )}
                              {t.state === 'PAUSED' ? (
                                <button 
                                  onClick={() => handleAction(t.tag, 'resume')}
                                  className="p-1.5 hover:bg-[var(--muted)] rounded-lg text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
                                  title="Resume"
                                >
                                  <Play className="w-4 h-4 fill-current" />
                                </button>
                              ) : t.state !== 'FAILED' && t.state !== 'RETRYING' && (
                                <button 
                                  onClick={() => handleAction(t.tag, 'pause')}
                                  className="p-1.5 hover:bg-[var(--muted)] rounded-lg text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
                                  title="Pause"
                                >
                                  <Pause className="w-4 h-4 fill-current" />
                                </button>
                              )}
                              <button 
                                onClick={() => handleAction(t.tag, 'cancel')}
                                className="p-1.5 hover:bg-rose-500/10 rounded-lg text-[var(--muted-foreground)] hover:text-rose-500 transition-colors"
                                title="Cancel"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                          <div className="h-2 bg-[var(--muted)] rounded-full overflow-hidden relative">
                            <motion.div 
                              className={`h-full rounded-full relative ${t.state === 'FAILED' ? 'bg-rose-500' : 'bg-blue-500'}`}
                              initial={{ width: 0 }}
                              animate={{ width: `${t.progress_pct}%` }}
                              transition={{ duration: 0.5, ease: "easeOut" }}
                            >
                              {t.state === 'ACTIVE' && (
                                <motion.div 
                                  className="absolute inset-0 bg-white/20"
                                  animate={{ x: ['-100%', '100%'] }}
                                  transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                                />
                              )}
                            </motion.div>
                          </div>
                        </div>
                        
                        {t.state === 'RETRYING' && t.progress_pct === 0 && (
                          <div className="mt-4 p-3 bg-orange-500/10 border border-orange-500/20 rounded-xl flex items-start gap-3">
                            <AlertCircle className="w-4 h-4 text-orange-400 shrink-0 mt-0.5" />
                            <p className="text-[11px] text-orange-200/70 leading-relaxed">
                              Stuck at 0%? Try <button onClick={() => handleAction(t.tag, 'resume')} className="text-orange-400 font-bold hover:underline">Resuming</button> or <button onClick={() => handleAction(t.tag, 'cancel')} className="text-orange-400 font-bold hover:underline">Restarting</button> the download.
                            </p>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))
                )}
              </AnimatePresence>
            </div>

            {/* Completed Section */}
            {completedTransfers.length > 0 && (
              <div className="pt-8 border-t border-[var(--border)]">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold flex items-center gap-2">
                    <button 
                      onClick={() => selectAll('completed')}
                      className="p-1 hover:bg-[var(--muted)] rounded transition-colors text-[var(--muted-foreground)]"
                      title="Select All Completed"
                    >
                      {completedTransfers.length > 0 && completedTransfers.every(t => selectedTransfers.has(t.tag)) ? (
                        <CheckSquare className="w-5 h-5 text-blue-500" />
                      ) : (
                        <Square className="w-5 h-5" />
                      )}
                    </button>
                    Completed
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    <span className="bg-emerald-500/10 text-emerald-500 text-[10px] px-2 py-0.5 rounded-full border border-emerald-500/20">
                      {completedTransfers.length}
                    </span>
                  </h2>
                </div>
                <div className="space-y-3">
                  {completedTransfers.map((t) => (
                    <div 
                      key={t.tag}
                      className={`bg-[var(--card)] border rounded-xl p-4 flex items-center justify-between gap-4 transition-all ${selectedTransfers.has(t.tag) ? 'border-blue-500 ring-1 ring-blue-500/20 opacity-100' : 'border-[var(--border)] opacity-80 hover:opacity-100'}`}
                    >
                      <div className="flex items-center gap-3 min-w-0 flex-1">
                        <button 
                          onClick={() => toggleSelect(t.tag)}
                          className="p-1 hover:bg-[var(--muted)] rounded transition-colors text-[var(--muted-foreground)]"
                        >
                          {selectedTransfers.has(t.tag) ? (
                            <CheckSquare className="w-5 h-5 text-blue-500" />
                          ) : (
                            <Square className="w-5 h-5" />
                          )}
                        </button>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-medium truncate text-[var(--foreground)]">{t.filename}</h3>
                          <p className="text-[10px] text-[var(--muted-foreground)] font-mono mt-0.5">{t.path}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-wider">
                          {t.size_bytes === 0 ? 'Unknown size' : formatBytes(t.size_bytes)}
                        </span>
                        <button 
                          onClick={() => handleDownload(undefined, t.url)}
                          className="p-1.5 hover:bg-blue-500/10 rounded-lg text-[var(--muted-foreground)] hover:text-blue-500 transition-colors"
                          title="Re-download"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => handleAction(t.tag, 'cancel')}
                          className="p-1.5 hover:bg-[var(--muted)] rounded-lg text-[var(--muted-foreground)] transition-colors"
                          title="Remove from list"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

          {activeTab === 'history' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between mb-2">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                History
                <History className="w-4 h-4 text-gray-500" />
              </h2>
              <div className="flex items-center gap-2">
                <button 
                  onClick={exportHistory}
                  className="p-1.5 hover:bg-[var(--muted)] rounded-lg text-[var(--muted-foreground)] hover:text-blue-500 transition-colors"
                  title="Export History"
                >
                  <DownloadCloud className="w-4 h-4" />
                </button>
                {history.length > 0 && (
                  <button 
                    onClick={clearHistory}
                    className="text-[10px] uppercase font-bold text-gray-500 hover:text-rose-400 flex items-center gap-1 transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                    {selectedHistory.size > 0 ? 'Clear Selected' : 'Clear All'}
                  </button>
                )}
              </div>
            </div>

            <div className="relative mb-4">
              <input
                type="text"
                value={historySearchQuery}
                onChange={(e) => setHistorySearchQuery(e.target.value)}
                placeholder="Search history..."
                className="w-full bg-[var(--card)] border border-[var(--border)] rounded-xl px-4 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all placeholder:text-[var(--muted-foreground)] text-[var(--foreground)]"
              />
              {historySearchQuery && (
                <button 
                  onClick={() => setHistorySearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-[var(--muted)] rounded-full text-[var(--muted-foreground)] transition-colors"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>

            <div className="bg-[var(--card)] border border-[var(--border)] rounded-2xl overflow-hidden shadow-sm">
              {filteredHistory.length === 0 ? (
                <div className="p-8 text-center text-[var(--muted-foreground)] text-sm italic">
                  {historySearchQuery ? 'No matches found' : 'No history yet'}
                </div>
              ) : (
                <div className="divide-y divide-[var(--border)]">
                  {filteredHistory.map((h, i) => (
                    <div key={i} className="flex items-center group">
                      <button
                        onClick={() => {
                          setSelectedHistory(prev => {
                            const next = new Set(prev);
                            if (next.has(h.url)) next.delete(h.url);
                            else next.add(h.url);
                            return next;
                          });
                        }}
                        className={`p-4 hover:bg-[var(--muted)] transition-colors ${selectedHistory.has(h.url) ? 'text-blue-500' : 'text-[var(--muted-foreground)]/40'}`}
                      >
                        {selectedHistory.has(h.url) ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4" />}
                      </button>
                      <button
                        onClick={() => setUrl(h.url)}
                        className="flex-1 text-left py-4 pr-4 hover:bg-[var(--muted)] transition-colors flex items-center justify-between gap-3 min-w-0"
                      >
                        <div className="flex flex-col min-w-0">
                          <span className="text-xs text-[var(--muted-foreground)] truncate group-hover:text-blue-500 transition-colors">
                            {h.url}
                          </span>
                          <span className="text-[9px] text-[var(--muted-foreground)]/40 mt-1">
                            {new Date(h.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <Plus className="w-3 h-3 text-[var(--muted-foreground)]/40 group-hover:text-blue-500 shrink-0" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

          {activeTab === 'analytics' && (
            <div className="space-y-8 max-w-6xl mx-auto w-full">
              {/* Analytics Dashboard */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-[var(--card)] border border-[var(--border)] p-6 rounded-3xl shadow-sm">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-blue-500/10 rounded-xl flex items-center justify-center text-blue-500">
                      <DownloadCloud className="w-5 h-5" />
                    </div>
                    <span className="text-xs font-bold text-[var(--muted-foreground)] uppercase tracking-wider">Total Downloaded</span>
                  </div>
                  <div className="text-3xl font-bold font-mono">{formatBytes(analytics?.total_downloaded_bytes || 0)}</div>
                </div>
                
                <div className="bg-[var(--card)] border border-[var(--border)] p-6 rounded-3xl shadow-sm">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-emerald-500/10 rounded-xl flex items-center justify-center text-emerald-500">
                      <CheckCircle2 className="w-5 h-5" />
                    </div>
                    <span className="text-xs font-bold text-[var(--muted-foreground)] uppercase tracking-wider">Completed</span>
                  </div>
                  <div className="text-3xl font-bold font-mono">{analytics?.total_transfers_completed || 0}</div>
                </div>

                <div className="bg-[var(--card)] border border-[var(--border)] p-6 rounded-3xl shadow-sm">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-rose-500/10 rounded-xl flex items-center justify-center text-rose-500">
                      <AlertCircle className="w-5 h-5" />
                    </div>
                    <span className="text-xs font-bold text-[var(--muted-foreground)] uppercase tracking-wider">Failed</span>
                  </div>
                  <div className="text-3xl font-bold font-mono">{analytics?.total_transfers_failed || 0}</div>
                </div>

                <div className="bg-[var(--card)] border border-[var(--border)] p-6 rounded-3xl shadow-sm">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-amber-500/10 rounded-xl flex items-center justify-center text-amber-500">
                      <Zap className="w-5 h-5" />
                    </div>
                    <span className="text-xs font-bold text-[var(--muted-foreground)] uppercase tracking-wider">Peak Speed</span>
                  </div>
                  <div className="text-3xl font-bold font-mono">{formatSpeed(analytics?.peak_speed_bps || 0)}</div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {(analytics?.daily_stats || []).some((d) => (d.bytes ?? 0) > 0 || (d.count ?? 0) > 0) ? (
                  <>
                    <div className="bg-[var(--card)] border border-[var(--border)] p-6 rounded-3xl shadow-sm">
                      <h3 className="text-sm font-bold mb-6 flex items-center gap-2">
                        <Activity className="w-4 h-4 text-blue-500" />
                        Download Activity (Last 7 Days)
                      </h3>
                      <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={analytics?.daily_stats || []}>
                            <defs>
                              <linearGradient id="colorBytes" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                            <XAxis 
                              dataKey="date" 
                              stroke="var(--muted-foreground)" 
                              fontSize={10} 
                              tickFormatter={(val) => val.split('-').slice(1).join('/')}
                            />
                            <YAxis 
                              stroke="var(--muted-foreground)" 
                              fontSize={10} 
                              tickFormatter={(val) => formatBytes(val).split(' ')[0]}
                            />
                            <Tooltip 
                              contentStyle={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)', borderRadius: '12px', fontSize: '12px' }}
                              formatter={(value: number) => [formatBytes(value), 'Downloaded']}
                            />
                            <Area type="monotone" dataKey="bytes" stroke="#3b82f6" fillOpacity={1} fill="url(#colorBytes)" strokeWidth={2} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    <div className="bg-[var(--card)] border border-[var(--border)] p-6 rounded-3xl shadow-sm">
                      <h3 className="text-sm font-bold mb-6 flex items-center gap-2">
                        <BarChart3 className="w-4 h-4 text-emerald-500" />
                        Transfers Completed
                      </h3>
                      <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={analytics?.daily_stats || []}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                            <XAxis 
                              dataKey="date" 
                              stroke="var(--muted-foreground)" 
                              fontSize={10} 
                              tickFormatter={(val) => val.split('-').slice(1).join('/')}
                            />
                            <YAxis stroke="var(--muted-foreground)" fontSize={10} />
                            <Tooltip 
                              contentStyle={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)', borderRadius: '12px', fontSize: '12px' }}
                            />
                            <Bar dataKey="count" fill="#10b981" radius={[4, 4, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="lg:col-span-2 bg-[var(--card)] border border-[var(--border)] border-dashed p-8 rounded-3xl text-center text-sm text-[var(--muted-foreground)]">
                    Daily charts appear after completed transfers are recorded (last 7 days). Active downloads still update the summary cards above.
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Collapsible Log */}
      <div className={`fixed bottom-0 left-0 right-0 z-40 transition-all duration-300 ease-in-out ${isLogExpanded ? 'h-80' : 'h-12'}`}>
        <div className="max-w-7xl mx-auto px-4 h-full">
          <div className="bg-[var(--card)] border-x border-t border-[var(--border)] rounded-t-2xl h-full flex flex-col shadow-2xl">
            <div className="flex items-center justify-between px-6 py-3 border-b border-[var(--border)] bg-[var(--muted)]/20">
              <div className="flex items-center gap-6">
                <button 
                  onClick={() => {
                    setIsLogExpanded(!isLogExpanded);
                    if (!isLogExpanded) setIsTerminalOpen(false);
                  }}
                  className={`flex items-center gap-3 transition-opacity ${!isTerminalOpen ? 'opacity-100' : 'opacity-40 hover:opacity-100'}`}
                >
                  <FileText className="w-4 h-4 text-blue-500" />
                  <span className="text-xs font-bold uppercase tracking-widest text-[var(--muted-foreground)]">System Log</span>
                </button>
                <button 
                  onClick={() => {
                    setIsLogExpanded(true);
                    setIsTerminalOpen(true);
                  }}
                  className={`flex items-center gap-3 transition-opacity ${isTerminalOpen ? 'opacity-100' : 'opacity-40 hover:opacity-100'}`}
                >
                  <Terminal className="w-4 h-4 text-emerald-500" />
                  <span className="text-xs font-bold uppercase tracking-widest text-[var(--muted-foreground)]">MEGA Terminal</span>
                </button>
                {isLogExpanded && isTerminalOpen && (
                  <button 
                    onClick={() => setTerminalOutput([])}
                    className="text-[10px] uppercase font-bold text-gray-500 hover:text-rose-400 transition-colors ml-4"
                  >
                    Clear Terminal
                  </button>
                )}
                {isLogExpanded ? (
                  <ChevronDown className="w-4 h-4 text-[var(--muted-foreground)] cursor-pointer" onClick={() => setIsLogExpanded(false)} />
                ) : (
                  <ChevronUp className="w-4 h-4 text-[var(--muted-foreground)] cursor-pointer" onClick={() => setIsLogExpanded(true)} />
                )}
              </div>
              
              {isLogExpanded && !isTerminalOpen && (
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2 bg-[var(--background)] border border-[var(--border)] rounded-lg px-2 py-1">
                    <Filter className="w-3 h-3 text-[var(--muted-foreground)]" />
                    <select 
                      value={logFilterLevel}
                      onChange={(e) => setLogFilterLevel(e.target.value as any)}
                      className="bg-transparent text-[10px] font-bold uppercase text-[var(--muted-foreground)] focus:outline-none cursor-pointer"
                    >
                      <option value="ALL">All Levels</option>
                      <option value="INFO">Info</option>
                      <option value="SUCCESS">Success</option>
                      <option value="WARN">Warning</option>
                      <option value="ERROR">Error</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-2 bg-[var(--background)] border border-[var(--border)] rounded-lg px-2 py-1">
                    <Tag className="w-3 h-3 text-[var(--muted-foreground)]" />
                    <select 
                      value={logFilterCategory}
                      onChange={(e) => setLogFilterCategory(e.target.value as any)}
                      className="bg-transparent text-[10px] font-bold uppercase text-[var(--muted-foreground)] focus:outline-none cursor-pointer"
                    >
                      <option value="ALL">All Categories</option>
                      <option value="SYSTEM">System</option>
                      <option value="TRANSFER">Transfer</option>
                      <option value="AUTOMATION">Automation</option>
                      <option value="AUTH">Auth</option>
                    </select>
                  </div>
                  <div className="relative">
                    <input
                      type="text"
                      value={logSearchQuery}
                      onChange={(e) => setLogSearchQuery(e.target.value)}
                      placeholder="Search logs..."
                      className="bg-[var(--background)] border border-[var(--border)] rounded-lg px-3 py-1 text-[10px] focus:outline-none focus:ring-1 focus:ring-blue-500/50 w-32"
                    />
                  </div>
                  <button 
                    onClick={exportLogs}
                    className="p-1 hover:bg-[var(--muted)] rounded text-[var(--muted-foreground)] hover:text-blue-500 transition-colors"
                    title="Export Logs"
                  >
                    <FileText className="w-4 h-4" />
                  </button>
                  <button 
                    onClick={clearLogs}
                    className="text-[10px] uppercase font-bold text-gray-500 hover:text-rose-400 transition-colors"
                  >
                    Clear
                  </button>
                </div>
              )}
            </div>
            
            {isLogExpanded && (
              <div className="flex-1 flex flex-col overflow-hidden">
                {isTerminalOpen ? (
                  <div className="flex-1 flex flex-col p-4 font-mono text-[11px] bg-black/20">
                    {/* Command Palette */}
                    <div className="flex flex-wrap gap-2 mb-4 p-3 bg-white/5 rounded-xl border border-white/10">
                      <button onClick={() => executeCommand('mega-whoami')} className="px-2 py-1 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded border border-blue-500/20 transition-colors flex items-center gap-1.5">
                        <User className="w-3 h-3" /> mega-whoami
                      </button>
                      <button onClick={() => executeCommand('mega-ls')} className="px-2 py-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded border border-emerald-500/20 transition-colors flex items-center gap-1.5">
                        <Filter className="w-3 h-3" /> mega-ls
                      </button>
                      <button onClick={() => executeCommand('mega-df')} className="px-2 py-1 bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 rounded border border-purple-500/20 transition-colors flex items-center gap-1.5">
                        <HardDrive className="w-3 h-3" /> mega-df
                      </button>
                      <button onClick={() => executeCommand('mega-export')} className="px-2 py-1 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 rounded border border-amber-500/20 transition-colors flex items-center gap-1.5">
                        <DownloadCloud className="w-3 h-3" /> mega-export
                      </button>
                      <button onClick={() => executeCommand('mega-transfers')} className="px-2 py-1 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 rounded border border-cyan-500/20 transition-colors flex items-center gap-1.5">
                        <Activity className="w-3 h-3" /> mega-transfers
                      </button>
                      <button onClick={() => executeCommand('mega-log')} className="px-2 py-1 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded border border-rose-500/20 transition-colors flex items-center gap-1.5">
                        <Zap className="w-3 h-3" /> mega-log
                      </button>
                      <div className="h-6 w-px bg-white/10 mx-1" />
                      <button 
                        onClick={() => {
                          const newEnabled = !config?.is_scheduling_enabled;
                          updateConfig({ is_scheduling_enabled: newEnabled });
                          executeCommand(`Scheduling ${newEnabled ? 'Enabled' : 'Disabled'}`);
                        }} 
                        className={`px-2 py-1 rounded border transition-colors flex items-center gap-1.5 ${config?.is_scheduling_enabled ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' : 'bg-white/5 text-white/40 border-white/10'}`}
                      >
                        <Timer className="w-3 h-3" /> Toggle Schedule
                      </button>
                      <button 
                        onClick={() => {
                          const newPrivacy = !config?.is_privacy_mode;
                          updateConfig({ is_privacy_mode: newPrivacy });
                          executeCommand(`Privacy Mode ${newPrivacy ? 'Enabled' : 'Disabled'}`);
                        }} 
                        className={`px-2 py-1 rounded border transition-colors flex items-center gap-1.5 ${config?.is_privacy_mode ? 'bg-rose-500/20 text-rose-400 border-rose-500/30' : 'bg-white/5 text-white/40 border-white/10'}`}
                      >
                        <ShieldCheck className="w-3 h-3" /> Privacy Mode
                      </button>
                      <button 
                        onClick={() => {
                          const newCompact = !config?.is_compact_mode;
                          updateConfig({ is_compact_mode: newCompact });
                          executeCommand(`Compact Mode ${newCompact ? 'Enabled' : 'Disabled'}`);
                        }} 
                        className={`px-2 py-1 rounded border transition-colors flex items-center gap-1.5 ${config?.is_compact_mode ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' : 'bg-white/5 text-white/40 border-white/10'}`}
                      >
                        <Filter className="w-3 h-3" /> Compact Mode
                      </button>
                    </div>

                    <div className="flex-1 overflow-y-auto custom-scrollbar space-y-2 mb-4">
                      <div className="text-emerald-500/60 font-bold">MEGAcmd Interactive Terminal v1.0.0</div>
                      <div className="text-white/40 italic">Type 'mega-help' for available commands.</div>
                      {terminalOutput.map((entry, i) => (
                        <div key={i} className="space-y-1 group/entry relative">
                          <div className="flex gap-2 text-emerald-400">
                            <span className="shrink-0">➜</span>
                            <span className="font-bold">{entry.cmd}</span>
                          </div>
                          <div className="pl-6 text-white/70 whitespace-pre-wrap relative">
                            {entry.out}
                            <button 
                              onClick={() => copyToClipboard(entry.out)}
                              className="absolute top-0 right-0 p-1 hover:bg-white/10 rounded opacity-0 group-hover/entry:opacity-100 transition-opacity"
                              title="Copy output"
                            >
                              <Copy className="w-3 h-3 text-white/40" />
                            </button>
                          </div>
                        </div>
                      ))}
                      <div ref={terminalEndRef} />
                    </div>

                    <form 
                      onSubmit={(e) => { e.preventDefault(); executeCommand(); }}
                      className="flex items-center gap-3 bg-black/40 border border-white/10 rounded-xl px-4 py-2 focus-within:ring-1 focus-within:ring-emerald-500/50 transition-all"
                    >
                      <span className="text-emerald-500 font-bold">➜</span>
                      <input 
                        type="text"
                        value={terminalInput}
                        onChange={(e) => setTerminalInput(e.target.value)}
                        placeholder="Enter MEGAcmd command..."
                        className="flex-1 bg-transparent border-none focus:outline-none text-white placeholder:text-white/20"
                      />
                      <button type="submit" className="p-1 hover:bg-white/10 rounded-lg text-emerald-500 transition-colors">
                        <Send className="w-4 h-4" />
                      </button>
                    </form>
                  </div>
                ) : (
                  <div className="flex-1 overflow-y-auto p-4 font-mono text-[11px] leading-relaxed text-[var(--muted-foreground)] custom-scrollbar">
                    {filteredLogs.length === 0 ? (
                      <div className="text-center py-10 opacity-40 italic">No matching logs found</div>
                    ) : (
                      filteredLogs.map((log, i) => (
                        <div key={i} className="mb-1 flex gap-3 group/log">
                          <span className="text-white/20 shrink-0">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                          <span className={`font-bold shrink-0 w-16 ${
                            log.level === 'ERROR' ? 'text-rose-500' : 
                            log.level === 'WARN' ? 'text-amber-500' : 
                            log.level === 'SUCCESS' ? 'text-emerald-500' : 
                            'text-blue-500'
                          }`}>
                            {log.level}
                          </span>
                          <span className="text-white/40 shrink-0 w-20 uppercase text-[9px] font-bold tracking-wider">
                            {log.category}
                          </span>
                          <span className={`flex-1 ${log.level === 'ERROR' ? 'text-rose-400' : 'text-white/70'}`}>
                            {log.message}
                            {log.tag && <span className="ml-2 px-1.5 py-0.5 bg-white/5 rounded text-[9px] text-white/30 font-bold uppercase tracking-tighter group-hover/log:text-blue-400 transition-colors">#{log.tag}</span>}
                          </span>
                        </div>
                      ))
                    )}
                    <div ref={logEndRef} />
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.2);
        }
      `}</style>

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
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-md bg-[var(--card)] border border-[var(--border)] rounded-3xl shadow-2xl overflow-hidden"
            >
              <div className="flex items-center justify-between px-8 py-6 border-b border-[var(--border)]">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-500/10 rounded-xl flex items-center justify-center">
                    <User className="w-5 h-5 text-blue-500" />
                  </div>
                  <h2 className="text-xl font-bold">Login to MEGA</h2>
                </div>
                <button 
                  onClick={() => setIsLoginOpen(false)}
                  className="p-2 hover:bg-[var(--muted)] rounded-xl text-[var(--muted-foreground)] transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleLogin} className="p-8 space-y-6">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-[var(--muted-foreground)] uppercase tracking-widest">Email Address</label>
                    <input
                      type="email"
                      required
                      value={loginEmail}
                      onChange={(e) => setLoginEmail(e.target.value)}
                      placeholder="your@email.com"
                      className="w-full bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
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
                      className="w-full bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
                    />
                  </div>
                </div>

                <div className="p-4 bg-blue-500/5 border border-blue-500/10 rounded-2xl">
                  <p className="text-[11px] text-[var(--muted-foreground)] leading-relaxed">
                    Your credentials are used only to authenticate with MEGAcmd. We do not store your password on our servers.
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold py-4 rounded-2xl shadow-lg shadow-blue-600/20 transition-all active:scale-[0.98] flex items-center justify-center gap-2"
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
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-2xl bg-[var(--card)] border border-[var(--border)] rounded-3xl shadow-2xl overflow-hidden"
            >
              <div className="flex items-center justify-between px-8 py-6 border-b border-[var(--border)]">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-500/10 rounded-xl flex items-center justify-center">
                    <Settings className="w-5 h-5 text-blue-500" />
                  </div>
                  <h2 className="text-xl font-bold">Advanced Settings</h2>
                </div>
                <button 
                  onClick={() => setIsSettingsOpen(false)}
                  className="p-2 hover:bg-[var(--muted)] rounded-xl transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-8 space-y-8 max-h-[70vh] overflow-y-auto custom-scrollbar">
                {/* General Settings */}
                <div className="space-y-4">
                  <h3 className="text-sm font-bold uppercase tracking-widest text-[var(--muted-foreground)] flex items-center gap-2">
                    <CloudDownload className="w-4 h-4" />
                    General
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-xs font-medium text-[var(--muted-foreground)]">Download Directory</label>
                      <input
                        type="text"
                        value={tempPath}
                        onChange={(e) => setTempPath(e.target.value)}
                        className="w-full bg-[var(--muted)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-medium text-[var(--muted-foreground)]">Concurrent Transfer Limit</label>
                      <input
                        type="number"
                        value={tempLimit}
                        onChange={(e) => setTempLimit(parseInt(e.target.value) || 1)}
                        className="w-full bg-[var(--muted)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                      />
                    </div>
                  </div>
                </div>

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
                        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none ${tempSoundAlertsEnabled ? 'bg-blue-600' : 'bg-[var(--muted)]'}`}
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
                          className="flex-1 bg-[var(--muted)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
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
                        className="w-full bg-[var(--muted)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
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
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${tempSchedulingEnabled ? 'bg-blue-600' : 'bg-[var(--muted)]'}`}
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
                        className="w-full bg-[var(--muted)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-medium text-[var(--muted-foreground)]">Stop Time</label>
                      <input
                        type="time"
                        value={tempScheduledStop}
                        onChange={(e) => setTempScheduledStop(e.target.value)}
                        className="w-full bg-[var(--muted)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
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
                        className="w-full bg-[var(--muted)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-medium text-[var(--muted-foreground)]">Retention (Days)</label>
                      <input
                        type="number"
                        value={tempRetentionDays}
                        onChange={(e) => setTempRetentionDays(parseInt(e.target.value) || 0)}
                        className="w-full bg-[var(--muted)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
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
                          className="w-full bg-[var(--muted)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
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
                          className="w-full bg-[var(--muted)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
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
                          className={`w-12 h-6 rounded-full transition-all relative ${tempWatchEnabled ? 'bg-blue-600' : 'bg-[var(--muted)]'}`}
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
                            className="w-full bg-[var(--background)] border border-[var(--border)] rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
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
                        className={`w-12 h-6 rounded-full transition-all relative ${tempPrivacyMode ? 'bg-blue-600' : 'bg-[var(--muted)]'}`}
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
                        className={`w-12 h-6 rounded-full transition-all relative ${tempCompactMode ? 'bg-blue-600' : 'bg-[var(--muted)]'}`}
                      >
                        <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${tempCompactMode ? 'right-1' : 'left-1'}`} />
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
                          <div className="w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center">
                            <User className="w-6 h-6 text-blue-500" />
                          </div>
                          <div>
                            <p className={`text-sm font-bold text-[var(--foreground)] ${config?.is_privacy_mode ? 'blur-sm select-none' : ''}`}>{accountInfo.email}</p>
                            <p className="text-[10px] font-bold text-blue-500 uppercase tracking-widest flex items-center gap-1 mt-0.5">
                              <ShieldCheck className="w-3 h-3" />
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
                              <HardDrive className="w-3.5 h-3.5 text-blue-500" />
                              Storage Usage
                            </div>
                            <span>{quotaPercent(accountInfo.storage_used_bytes, accountInfo.storage_total_bytes)}%</span>
                          </div>
                          <div className="w-full h-2 bg-[var(--background)] rounded-full overflow-hidden border border-[var(--border)]">
                            <motion.div 
                              initial={{ width: 0 }}
                              animate={{ width: `${quotaBarWidthPct(accountInfo.storage_used_bytes, accountInfo.storage_total_bytes)}%` }}
                              className="h-full bg-blue-500"
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
                                <ArrowUpDown className="w-3.5 h-3.5 text-blue-500" />
                                Bandwidth Quota
                              </div>
                              <span>{quotaPercent(accountInfo.bandwidth_used_bytes, accountInfo.bandwidth_limit_bytes)}%</span>
                            </div>
                            <div className="w-full h-2 bg-[var(--background)] rounded-full overflow-hidden border border-[var(--border)]">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${quotaBarWidthPct(accountInfo.bandwidth_used_bytes, accountInfo.bandwidth_limit_bytes)}%` }}
                                className="h-full bg-blue-500"
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
                        className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-blue-500/20"
                      >
                        Login to MEGA
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <div className="p-8 border-t border-[var(--border)] bg-[var(--muted)]/30 flex items-center justify-end gap-4">
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
                  className="px-8 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-bold shadow-lg shadow-blue-500/20 transition-all active:scale-95"
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
