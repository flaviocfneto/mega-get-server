import {render, screen} from '@testing-library/react';
import {describe, expect, it, vi} from 'vitest';
import {TransfersView} from './TransfersView';
import type {AppConfig, Transfer} from '../types';

const noop = () => {};
const config: AppConfig = {
  download_dir: '/data',
  poll_interval: 5,
  transfer_limit: 2,
  history_limit: 50,
  history_retention_days: 7,
  max_retries: 3,
  global_speed_limit_kbps: 0,
  is_scheduling_enabled: false,
  scheduled_start: '00:00',
  scheduled_stop: '23:59',
  sound_alerts_enabled: true,
  is_privacy_mode: false,
  is_compact_mode: false,
  post_download_action: '',
  webhook_url: '',
  watch_folder_enabled: false,
  watch_folder_path: '',
};

const baseProps = {
  transfers: [] as Transfer[],
  sortedTransfers: [] as Transfer[],
  completedTransfers: [] as Transfer[],
  config,
  selectedTransfers: new Set<string>(),
  toggleSelect: noop,
  selectAll: noop as (s: 'active' | 'completed') => void,
  handleBulkAction: noop as any,
  handleAction: noop as any,
  handleSetSpeedLimit: noop as any,
  handleDownload: noop as any,
  filterState: 'ALL' as const,
  setFilterState: noop as any,
  filterPriority: 'ALL' as const,
  setFilterPriority: noop as any,
  filterLabel: 'ALL',
  setFilterLabel: noop as any,
  sortBy: 'filename' as const,
  setSortBy: noop as any,
  sortOrder: 'asc' as const,
  setSortOrder: noop as any,
  setSelectedTransfers: noop as any,
};

const sampleTransfer: Transfer = {
  tag: '1',
  url: 'https://mega.nz/file/x',
  progress_pct: 50,
  downloaded_bytes: 500,
  speed_bps: 100,
  state: 'ACTIVE',
  path: '/data/x.zip',
  filename: 'x.zip',
  size_bytes: 1000,
};

describe('TransfersView', () => {
  it('renders empty active transfers', () => {
    render(<TransfersView {...baseProps} />);
    expect(screen.getByText('Active transfers')).toBeInTheDocument();
    expect(screen.getByText('No active transfers')).toBeInTheDocument();
  });

  it('lists active transfer rows and completed section', () => {
    const completed: Transfer = {
      ...sampleTransfer,
      tag: '9',
      state: 'COMPLETED',
      progress_pct: 100,
      filename: 'done.zip',
    };
    render(
      <TransfersView
        {...baseProps}
        transfers={[sampleTransfer, completed]}
        sortedTransfers={[sampleTransfer]}
        completedTransfers={[completed]}
        selectedTransfers={new Set(['1'])}
      />,
    );
    expect(screen.getByText('x.zip')).toBeInTheDocument();
    expect(screen.getByRole('heading', {name: /completed/i})).toBeInTheDocument();
    expect(screen.getByText(/1 selected/i)).toBeInTheDocument();
  });
});
