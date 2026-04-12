import {fireEvent, render, screen} from '@testing-library/react';
import {describe, expect, it, vi} from 'vitest';
import {TransfersBulkBar} from './TransfersBulkBar';

describe('TransfersBulkBar', () => {
  it('renders nothing when count is 0', () => {
    const {container} = render(
      <TransfersBulkBar
        count={0}
        onPause={vi.fn()}
        onResume={vi.fn()}
        onCancel={vi.fn()}
        onRedownload={vi.fn()}
        onSetPriority={vi.fn()}
        onDeselectAll={vi.fn()}
      />,
    );
    expect(container.textContent).toBe('');
  });

  it('invokes handlers when visible', () => {
    const onPause = vi.fn();
    const onSetPriority = vi.fn();
    const onDeselectAll = vi.fn();
    render(
      <TransfersBulkBar
        count={2}
        onPause={onPause}
        onResume={vi.fn()}
        onCancel={vi.fn()}
        onRedownload={vi.fn()}
        onSetPriority={onSetPriority}
        onDeselectAll={onDeselectAll}
      />,
    );
    expect(screen.getByText(/2 selected/i)).toBeInTheDocument();
    fireEvent.click(screen.getByTitle('Pause selected'));
    expect(onPause).toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', {name: 'HIGH'}));
    expect(onSetPriority).toHaveBeenCalledWith('HIGH');
    fireEvent.click(screen.getByRole('button', {name: /deselect all/i}));
    expect(onDeselectAll).toHaveBeenCalled();
  });
});
