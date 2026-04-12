import {fireEvent, render, screen} from '@testing-library/react';
import {describe, expect, it, vi} from 'vitest';
import {PendingQueuePanel} from './PendingQueuePanel';
import type {PendingQueueItem} from '../../types';

const item = (over: Partial<PendingQueueItem> = {}): PendingQueueItem => ({
  id: '00000000-0000-4000-8000-000000000099',
  url: 'https://example.com/file',
  tags: ['a'],
  priority: 'NORMAL',
  created_at: '2026-01-01T00:00:00Z',
  status: 'PENDING',
  last_error: null,
  ...over,
});

describe('PendingQueuePanel', () => {
  it('shows empty hint', () => {
    render(
      <PendingQueuePanel
        items={[]}
        busy={false}
        onRemove={vi.fn()}
        onStart={vi.fn()}
        onStartNext={vi.fn()}
        onStartAll={vi.fn()}
      />,
    );
    expect(screen.getByText(/no saved links/i)).toBeInTheDocument();
  });

  it('starts next and removes rows', () => {
    const onStartNext = vi.fn();
    const onRemove = vi.fn();
    const items = [item(), item({id: '00000000-0000-4000-8000-0000000000aa', status: 'FAILED', last_error: 'boom'})];
    render(
      <PendingQueuePanel
        items={items}
        busy={false}
        onRemove={onRemove}
        onStart={vi.fn()}
        onStartNext={onStartNext}
        onStartAll={vi.fn()}
        headingLevel="h1"
        title="Queue test"
      />,
    );
    expect(screen.getByRole('heading', {level: 1, name: 'Queue test'})).toBeInTheDocument();
    expect(screen.getByText('boom')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', {name: /start next/i}));
    expect(onStartNext).toHaveBeenCalled();
    const removeButtons = screen.getAllByRole('button', {name: /remove/i});
    fireEvent.click(removeButtons[0]!);
    expect(onRemove).toHaveBeenCalled();
  });

  it('hides remove while dispatching', () => {
    render(
      <PendingQueuePanel
        items={[item({status: 'DISPATCHING'})]}
        busy={false}
        onRemove={vi.fn()}
        onStart={vi.fn()}
        onStartNext={vi.fn()}
        onStartAll={vi.fn()}
      />,
    );
    expect(screen.queryByRole('button', {name: /remove/i})).toBeNull();
  });
});
