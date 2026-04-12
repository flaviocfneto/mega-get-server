import type {
  AnalyticsData,
  AppConfig,
  HistoryItem,
  LogEntry,
  LogCategory,
  LogLevel,
  ToolDiagnosticEntry,
  ToolDiagnosticsReport,
  Transfer,
  TransferDriver,
  AccountInfo,
  PendingQueueItem,
  PendingQueueStatus,
  TransferPriority,
} from './types';

export const DEFAULT_APP_CONFIG: AppConfig = {
  download_dir: '',
  poll_interval: 1000,
  transfer_limit: 50,
  history_limit: 50,
  history_retention_days: 7,
  max_retries: 3,
  global_speed_limit_kbps: 0,
  scheduled_start: '00:00',
  scheduled_stop: '23:59',
  is_scheduling_enabled: false,
  sound_alerts_enabled: true,
  is_privacy_mode: false,
  is_compact_mode: false,
  post_download_action: '',
  webhook_url: '',
  watch_folder_enabled: false,
  watch_folder_path: '/downloads/watch',
};

const LOG_LEVELS = new Set<LogLevel>(['INFO', 'WARN', 'ERROR', 'SUCCESS']);
const LOG_CATEGORIES = new Set<LogCategory>(['SYSTEM', 'TRANSFER', 'AUTOMATION', 'AUTH']);
const PENDING_QUEUE_STATUS = new Set<PendingQueueStatus>(['PENDING', 'DISPATCHING', 'FAILED']);
const PRIORITIES = new Set<TransferPriority>(['LOW', 'NORMAL', 'HIGH']);
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function asString(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback;
}

function asNumber(value: unknown, fallback = 0): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function asBoolean(value: unknown, fallback = false): boolean {
  return typeof value === 'boolean' ? value : fallback;
}

export function mergeAppConfig(data: unknown): AppConfig {
  const src = isRecord(data) ? data : {};
  return {
    download_dir: asString(src.download_dir, DEFAULT_APP_CONFIG.download_dir),
    poll_interval: asNumber(src.poll_interval, DEFAULT_APP_CONFIG.poll_interval),
    transfer_limit: asNumber(src.transfer_limit, DEFAULT_APP_CONFIG.transfer_limit),
    history_limit: asNumber(src.history_limit, DEFAULT_APP_CONFIG.history_limit),
    history_retention_days: asNumber(src.history_retention_days, DEFAULT_APP_CONFIG.history_retention_days),
    max_retries: asNumber(src.max_retries, DEFAULT_APP_CONFIG.max_retries),
    global_speed_limit_kbps: asNumber(src.global_speed_limit_kbps, DEFAULT_APP_CONFIG.global_speed_limit_kbps),
    scheduled_start: asString(src.scheduled_start, DEFAULT_APP_CONFIG.scheduled_start),
    scheduled_stop: asString(src.scheduled_stop, DEFAULT_APP_CONFIG.scheduled_stop),
    is_scheduling_enabled: asBoolean(src.is_scheduling_enabled, DEFAULT_APP_CONFIG.is_scheduling_enabled),
    sound_alerts_enabled: asBoolean(src.sound_alerts_enabled, DEFAULT_APP_CONFIG.sound_alerts_enabled),
    is_privacy_mode: asBoolean(src.is_privacy_mode, DEFAULT_APP_CONFIG.is_privacy_mode),
    is_compact_mode: asBoolean(src.is_compact_mode, DEFAULT_APP_CONFIG.is_compact_mode),
    post_download_action: asString(src.post_download_action, DEFAULT_APP_CONFIG.post_download_action),
    webhook_url: asString(src.webhook_url, DEFAULT_APP_CONFIG.webhook_url),
    watch_folder_enabled: asBoolean(src.watch_folder_enabled, DEFAULT_APP_CONFIG.watch_folder_enabled),
    watch_folder_path: asString(src.watch_folder_path, DEFAULT_APP_CONFIG.watch_folder_path),
  };
}

export function normalizeHistory(data: unknown): HistoryItem[] {
  if (!Array.isArray(data)) return [];
  if (data.length === 0) return [];
  const first = data[0];
  if (typeof first === 'string') {
    return data.filter((url): url is string => typeof url === 'string').map((url) => ({
      url,
      timestamp: new Date(0).toISOString(),
    }));
  }
  return data
    .filter((item): item is Record<string, unknown> => isRecord(item))
    .map((item) => ({
      url: asString(item.url),
      timestamp: asString(item.timestamp, new Date(0).toISOString()),
    }))
    .filter((item) => item.url.length > 0);
}

export function normalizeLogs(data: unknown): LogEntry[] {
  if (!Array.isArray(data)) return [];
  if (data.length === 0) return [];
  const first = data[0];
  if (typeof first === 'string') {
    return data.filter((message): message is string => typeof message === 'string').map((message) => ({
      timestamp: new Date().toISOString(),
      level: 'INFO',
      category: 'SYSTEM',
      message,
    }));
  }
  return data
    .filter((item): item is Record<string, unknown> => isRecord(item))
    .map((item) => ({
      timestamp: asString(item.timestamp, new Date().toISOString()),
      level: LOG_LEVELS.has(item.level as LogLevel) ? (item.level as LogLevel) : 'INFO',
      category: LOG_CATEGORIES.has(item.category as LogCategory) ? (item.category as LogCategory) : 'SYSTEM',
      message: asString(item.message),
      tag: typeof item.tag === 'string' ? item.tag : undefined,
    }))
    .filter((item) => item.message.length > 0);
}

export function normalizeTransfers(data: unknown): Transfer[] {
  if (!Array.isArray(data)) return [];
  return data
    .filter((item): item is Record<string, unknown> => isRecord(item))
    .map((item) => {
      const d = item.driver;
      const driver: TransferDriver | undefined =
        d === 'http' || d === 'megacmd' ? (d as TransferDriver) : undefined;
      return {
        tag: asString(item.tag),
        url: asString(item.url),
        progress_pct: asNumber(item.progress_pct),
        downloaded_bytes: asNumber(item.downloaded_bytes),
        speed_bps: asNumber(item.speed_bps),
        state: asString(item.state, 'QUEUED') as Transfer['state'],
        path: asString(item.path),
        filename: asString(item.filename),
        size_bytes: asNumber(item.size_bytes),
        retry_count: typeof item.retry_count === 'number' ? item.retry_count : undefined,
        speed_limit_kbps: typeof item.speed_limit_kbps === 'number' ? item.speed_limit_kbps : undefined,
        tags: Array.isArray(item.tags) ? item.tags.filter((t): t is string => typeof t === 'string') : undefined,
        priority: ['LOW', 'NORMAL', 'HIGH'].includes(asString(item.priority)) ? (item.priority as Transfer['priority']) : undefined,
        driver,
      };
    })
    .filter((item) => item.tag.length > 0);
}

export function normalizeAnalytics(data: unknown): AnalyticsData {
  const src = isRecord(data) ? data : {};
  const dailyRaw = Array.isArray(src.daily_stats) ? src.daily_stats : [];
  return {
    total_downloaded_bytes: asNumber(src.total_downloaded_bytes),
    total_transfers_completed: asNumber(src.total_transfers_completed),
    total_transfers_failed: asNumber(src.total_transfers_failed),
    average_speed_bps: asNumber(src.average_speed_bps),
    uptime_seconds: asNumber(src.uptime_seconds),
    daily_stats: dailyRaw
      .filter((item): item is Record<string, unknown> => isRecord(item))
      .map((item) => ({
        date: asString(item.date),
        bytes: asNumber(item.bytes),
        count: asNumber(item.count),
      })),
  };
}

export function normalizeAccountInfo(data: unknown): AccountInfo {
  const src = isRecord(data) ? data : {};
  const acctType = asString(src.account_type, 'UNKNOWN');
  return {
    email: typeof src.email === 'string' ? src.email : null,
    is_logged_in: asBoolean(src.is_logged_in),
    account_type: ['FREE', 'PRO', 'BUSINESS', 'UNKNOWN'].includes(acctType)
      ? (acctType as AccountInfo['account_type'])
      : 'UNKNOWN',
    storage_used_bytes: asNumber(src.storage_used_bytes),
    storage_total_bytes: asNumber(src.storage_total_bytes),
    bandwidth_limit_bytes: asNumber(src.bandwidth_limit_bytes),
    bandwidth_used_bytes: asNumber(src.bandwidth_used_bytes),
    details_partial: typeof src.details_partial === 'boolean' ? src.details_partial : undefined,
  };
}

function normalizeToolEntry(data: unknown): ToolDiagnosticEntry | null {
  if (!isRecord(data)) return null;
  return {
    name: asString(data.name),
    available: asBoolean(data.available),
    detected_version: typeof data.detected_version === 'string' ? data.detected_version : undefined,
    required_for: Array.isArray(data.required_for) ? data.required_for.filter((x): x is string => typeof x === 'string') : undefined,
    install_instructions: typeof data.install_instructions === 'string' ? data.install_instructions : undefined,
    suggested_install_commands: Array.isArray(data.suggested_install_commands)
      ? data.suggested_install_commands.filter((x): x is string => typeof x === 'string')
      : undefined,
    details: isRecord(data.details) ? data.details : undefined,
  };
}

export function normalizeToolDiagnostics(data: unknown): ToolDiagnosticsReport {
  const src = isRecord(data) ? data : {};
  const tools = Array.isArray(src.tools) ? src.tools.map(normalizeToolEntry).filter((x): x is ToolDiagnosticEntry => x !== null) : [];
  return {
    ok: asBoolean(src.ok),
    missing_tools: Array.isArray(src.missing_tools) ? src.missing_tools.filter((x): x is string => typeof x === 'string') : [],
    tools,
  };
}

/** POST /api/login */
export interface LoginPostPayload {
  status: 'success' | 'error';
  message: string;
  account: AccountInfo | null;
}

export function normalizeLoginPostResponse(data: unknown): LoginPostPayload {
  const src = isRecord(data) ? data : {};
  const status = src.status === 'success' || src.status === 'error' ? src.status : 'error';
  const message = typeof src.message === 'string' ? src.message : '';
  const accountRaw = src.account;
  const account =
    accountRaw === undefined || accountRaw === null ? null : normalizeAccountInfo(accountRaw);
  return { status, message, account };
}

/** POST /api/terminal */
export interface TerminalPostPayload {
  ok: boolean;
  output: string;
  blocked_reason?: string;
  exit_code?: number;
}

export function normalizeTerminalPostResponse(data: unknown): TerminalPostPayload {
  const src = isRecord(data) ? data : {};
  return {
    ok: Boolean(src.ok),
    output: typeof src.output === 'string' ? src.output : '',
    blocked_reason: typeof src.blocked_reason === 'string' ? src.blocked_reason : undefined,
    exit_code: typeof src.exit_code === 'number' ? src.exit_code : undefined,
  };
}

export function normalizePendingQueueItem(data: unknown): PendingQueueItem | null {
  if (!isRecord(data)) return null;
  const id = asString(data.id);
  const url = asString(data.url);
  if (!id || !url) return null;
  const st = asString(data.status, 'PENDING').toUpperCase();
  const status: PendingQueueStatus = PENDING_QUEUE_STATUS.has(st as PendingQueueStatus) ? (st as PendingQueueStatus) : 'PENDING';
  const prRaw = asString(data.priority, 'NORMAL').toUpperCase();
  const priority: TransferPriority = PRIORITIES.has(prRaw as TransferPriority) ? (prRaw as TransferPriority) : 'NORMAL';
  const tagsRaw = data.tags;
  const tags =
    Array.isArray(tagsRaw) && tagsRaw.every((t) => typeof t === 'string')
      ? (tagsRaw as string[]).map((t) => t.trim()).filter(Boolean)
      : [];
  const le = data.last_error;
  const last_error = le === null || le === undefined ? null : typeof le === 'string' ? le : null;
  return {
    id,
    url,
    tags,
    priority,
    created_at: asString(data.created_at, new Date(0).toISOString()),
    status,
    last_error,
  };
}

export function normalizePendingQueueList(data: unknown): PendingQueueItem[] {
  if (!Array.isArray(data)) return [];
  return data.map(normalizePendingQueueItem).filter((x): x is PendingQueueItem => x !== null);
}

/** POST /api/download */
export interface DownloadPostPayload {
  success: boolean;
  message: string;
  detail?: string;
  queued?: boolean;
  item?: PendingQueueItem;
}

export function normalizeDownloadPostResponse(data: unknown): DownloadPostPayload {
  const src = isRecord(data) ? data : {};
  const itemRaw = src.item;
  let item: PendingQueueItem | undefined;
  if (itemRaw !== undefined && itemRaw !== null) {
    const parsed = normalizePendingQueueItem(itemRaw);
    if (parsed) item = parsed;
  }
  return {
    success: Boolean(src.success),
    message: typeof src.message === 'string' ? src.message : '',
    detail: typeof src.detail === 'string' ? src.detail : undefined,
    queued: typeof src.queued === 'boolean' ? src.queued : false,
    item,
  };
}

/** POST /api/transfers/bulk */
export interface BulkPostPayload {
  affectedCount: number;
  detail?: string;
}

export function normalizeBulkPostResponse(data: unknown): BulkPostPayload {
  const src = isRecord(data) ? data : {};
  return {
    affectedCount: asNumber(src.affectedCount),
    detail: typeof src.detail === 'string' ? src.detail : undefined,
  };
}

/** POST /api/transfers/{tag}/limit */
export interface SpeedLimitPostPayload {
  message: string;
  applied_to_megacmd?: boolean;
  detail?: string;
}

export function normalizeSpeedLimitPostResponse(data: unknown): SpeedLimitPostPayload {
  const src = isRecord(data) ? data : {};
  return {
    message: typeof src.message === 'string' ? src.message : '',
    applied_to_megacmd: typeof src.applied_to_megacmd === 'boolean' ? src.applied_to_megacmd : undefined,
    detail: typeof src.detail === 'string' ? src.detail : undefined,
  };
}
