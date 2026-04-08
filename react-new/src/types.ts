export type TransferPriority = 'LOW' | 'NORMAL' | 'HIGH';
export type TransferState = 'ACTIVE' | 'QUEUED' | 'PAUSED' | 'RETRYING' | 'COMPLETED' | 'FAILED';

export interface Transfer {
  tag: string;
  url: string;
  progress_pct: number;
  downloaded_bytes: number;
  speed_bps: number;
  state: TransferState;
  path: string;
  filename: string;
  size_bytes: number;
  retry_count?: number;
  speed_limit_kbps?: number;
  tags?: string[];
  priority?: TransferPriority;
}

export interface HistoryItem {
  url: string;
  timestamp: string;
}

export interface AppConfig {
  download_dir: string;
  poll_interval: number;
  transfer_limit: number;
  history_limit: number;
  history_retention_days: number;
  max_retries: number;
  global_speed_limit_kbps: number;
  scheduled_start?: string; // HH:mm
  scheduled_stop?: string; // HH:mm
  is_scheduling_enabled: boolean;
  sound_alerts_enabled: boolean;
  is_privacy_mode?: boolean;
  is_compact_mode?: boolean;
  post_download_action?: string;
  webhook_url?: string;
  watch_folder_enabled?: boolean;
  watch_folder_path?: string;
}

export type LogLevel = 'INFO' | 'WARN' | 'ERROR' | 'SUCCESS';
export type LogCategory = 'SYSTEM' | 'TRANSFER' | 'AUTOMATION' | 'AUTH';

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  category: LogCategory;
  message: string;
  tag?: string; // Optional transfer tag
}

export interface AnalyticsData {
  total_downloaded_bytes: number;
  total_transfers_completed: number;
  total_transfers_failed: number;
  average_speed_bps: number;
  peak_speed_bps: number;
  uptime_seconds: number;
  daily_stats: {
    date: string;
    bytes: number;
    count: number;
  }[];
}

export interface AccountInfo {
  email: string | null;
  is_logged_in: boolean;
  account_type: 'FREE' | 'PRO' | 'BUSINESS' | 'UNKNOWN';
  storage_used_bytes: number;
  storage_total_bytes: number;
  bandwidth_limit_bytes: number;
  bandwidth_used_bytes: number;
  details_partial?: boolean;
}

export interface ToolDiagnosticEntry {
  name: string;
  available: boolean;
  detected_version?: string;
  required_for?: string[];
  install_instructions?: string;
  suggested_install_commands?: string[];
  details?: Record<string, unknown>;
}

export interface ToolDiagnosticsReport {
  ok: boolean;
  missing_tools: string[];
  tools: ToolDiagnosticEntry[];
}
