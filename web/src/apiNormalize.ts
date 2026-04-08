import type { AppConfig, HistoryItem, LogEntry, LogCategory, LogLevel } from './types';

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

export function mergeAppConfig(data: Partial<AppConfig> | Record<string, unknown>): AppConfig {
  return { ...DEFAULT_APP_CONFIG, ...data } as AppConfig;
}

export function normalizeHistory(data: unknown): HistoryItem[] {
  if (!Array.isArray(data)) return [];
  if (data.length === 0) return [];
  const first = data[0];
  if (typeof first === 'string') {
    return (data as string[]).map((url) => ({
      url,
      timestamp: new Date(0).toISOString(),
    }));
  }
  return data as HistoryItem[];
}

export function normalizeLogs(data: unknown): LogEntry[] {
  if (!Array.isArray(data)) return [];
  if (data.length === 0) return [];
  const first = data[0];
  if (typeof first === 'string') {
    return (data as string[]).map((message) => ({
      timestamp: new Date().toISOString(),
      level: 'INFO' as LogLevel,
      category: 'SYSTEM' as LogCategory,
      message,
    }));
  }
  return data as LogEntry[];
}
