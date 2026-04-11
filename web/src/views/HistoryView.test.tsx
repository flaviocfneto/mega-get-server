import {render, screen} from '@testing-library/react';
import {describe, expect, it, vi} from 'vitest';
import type {PendingQueueItem} from '../types';
import {HistoryView} from './HistoryView';

const noop = () => {};

const queueProps = {
  pendingQueue: [] as PendingQueueItem[],
  queuePanelBusy: false,
  onQueueRemove: noop,
  onQueueStart: noop,
  onQueueStartNext: noop,
  onQueueStartAll: noop,
};

describe('HistoryView', () => {
  it('renders empty state when no history', () => {
    render(
      <HistoryView
        history={[]}
        filteredHistory={[]}
        historySearchQuery=""
        setHistorySearchQuery={vi.fn()}
        selectedHistory={new Set()}
        setSelectedHistory={vi.fn()}
        setUrl={vi.fn()}
        exportHistory={vi.fn()}
        clearHistory={vi.fn()}
        {...queueProps}
      />,
    );
    expect(screen.getByRole('heading', {name: 'History and Queue Management'})).toBeInTheDocument();
    expect(screen.getByRole('heading', {name: 'Download History'})).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Search history/)).toBeInTheDocument();
  });

  it('shows filtered rows when history exists', () => {
    const item = {url: 'https://mega.nz/file/x', timestamp: new Date().toISOString()};
    render(
      <HistoryView
        history={[item]}
        filteredHistory={[item]}
        historySearchQuery=""
        setHistorySearchQuery={vi.fn()}
        selectedHistory={new Set()}
        setSelectedHistory={vi.fn()}
        setUrl={vi.fn()}
        exportHistory={vi.fn()}
        clearHistory={vi.fn()}
        {...queueProps}
      />,
    );
    expect(screen.getByText('https://mega.nz/file/x')).toBeInTheDocument();
  });
});
