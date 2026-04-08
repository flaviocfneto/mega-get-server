export type TransferState = 'ACTIVE' | 'QUEUED' | 'PAUSED' | 'RETRYING' | 'COMPLETED' | 'FAILED';

export interface Transfer {
  tag: string;
  progress_pct: number;
  downloaded_bytes: number;
  state: TransferState;
  path: string;
  filename: string;
  size_bytes: number;
}

export interface AppConfig {
  download_dir: string;
  poll_interval: number;
  transfer_limit: number;
}
