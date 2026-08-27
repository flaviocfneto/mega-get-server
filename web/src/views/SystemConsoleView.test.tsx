import {render, screen} from '@testing-library/react';
import {describe, expect, it, vi} from 'vitest';
import {SystemConsoleView} from './SystemConsoleView';
import type {AppConfig} from '../types';

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
  isTerminalOpen: false,
  setIsTerminalOpen: noop,
  filteredLogs: [],
  logFilterLevel: 'ALL' as const,
  setLogFilterLevel: noop,
  logFilterCategory: 'ALL' as const,
  setLogFilterCategory: noop,
  logSearchQuery: '',
  setLogSearchQuery: noop,
  exportLogs: noop,
  clearLogs: noop,
  terminalOutput: [],
  terminalInput: '',
  setTerminalInput: noop,
  executeCommand: noop,
  clearTerminalOutput: noop,
  terminalEndRef: {current: null},
  logEndRef: {current: null},
  config,
  updateConfig: noop,
};

describe('SystemConsoleView', () => {
  it('renders accessible controls in log view', () => {
    render(<SystemConsoleView {...baseProps} />);
    expect(screen.getByRole('button', {name: /export logs/i})).toBeInTheDocument();
  });

  it('renders accessible controls and inputs in terminal view', () => {
    render(<SystemConsoleView {...baseProps} isTerminalOpen={true} />);
    expect(screen.getByRole('textbox', {name: /megacmd command/i})).toBeInTheDocument();
    expect(screen.getByRole('button', {name: /execute command/i})).toBeInTheDocument();
  });
});
