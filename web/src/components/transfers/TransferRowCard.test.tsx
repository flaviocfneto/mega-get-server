import {fireEvent, render, screen} from '@testing-library/react';
import {describe, expect, it, vi} from 'vitest';
import {TransferRowCard} from './TransferRowCard';
import type {AppConfig, Transfer} from '../../types';

const config: AppConfig = {
  download_dir: '/data',
  poll_interval: 1000,
  transfer_limit: 10,
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

const baseTransfer: Transfer = {
  tag: 'h-550e8400-e29b-41d4-a716-446655440000',
  url: 'https://example.com/a.bin',
  progress_pct: 40,
  downloaded_bytes: 400,
  speed_bps: 0,
  state: 'ACTIVE',
  path: '/data/a.bin',
  filename: 'a.bin',
  size_bytes: 1000,
  tags: ['one'],
  priority: 'HIGH',
  driver: 'http',
};

describe('TransferRowCard', () => {
  it('shows HTTP badge and fires actions', () => {
    const onAction = vi.fn();
    const onToggle = vi.fn();
    render(
      <TransferRowCard
        transfer={baseTransfer}
        config={config}
        selected={false}
        onToggleSelect={onToggle}
        onAction={onAction}
        onSetSpeedLimit={vi.fn()}
        reduceMotion
      />,
    );
    expect(screen.getByText('HTTP')).toBeInTheDocument();
    expect(screen.getByText('HIGH')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', {name: /select transfer/i}));
    expect(onToggle).toHaveBeenCalled();
    fireEvent.click(screen.getByTitle('Pause'));
    expect(onAction).toHaveBeenCalledWith('pause');
  });

  it('shows retry affordance for FAILED', () => {
    const onAction = vi.fn();
    render(
      <TransferRowCard
        transfer={{...baseTransfer, state: 'FAILED', progress_pct: 0}}
        config={config}
        selected={false}
        onToggleSelect={vi.fn()}
        onAction={onAction}
        onSetSpeedLimit={vi.fn()}
        reduceMotion
      />,
    );
    fireEvent.click(screen.getByTitle('Retry'));
    expect(onAction).toHaveBeenCalledWith('retry');
  });
});
