import {describe, expect, it, vi} from 'vitest';
import {fireEvent, render, screen} from '@testing-library/react';
import {SidebarNav} from './SidebarNav';
import {BottomNav} from './BottomNav';

describe('SidebarNav', () => {
  it('calls onSelect with section id and sets aria-current on active item', () => {
    const onSelect = vi.fn();
    render(<SidebarNav activeId="transfers" onSelect={onSelect} />);

    expect(screen.getByRole('navigation', {name: 'Primary'})).toBeInTheDocument();

    expect(screen.getByRole('button', {name: 'Transfers'})).toHaveAttribute('aria-current', 'page');
    const historyBtn = screen.getByRole('button', {name: 'History and Queue'});
    expect(historyBtn).not.toHaveAttribute('aria-current');
    fireEvent.click(historyBtn);
    expect(onSelect).toHaveBeenCalledWith('history');
  });

  it('includes Logs & Terminal primary section and title tooltip attributes', () => {
    render(<SidebarNav activeId="transfers" onSelect={vi.fn()} />);
    const button = screen.getByRole('button', {name: 'Logs & Terminal'});
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('title', 'Logs & Terminal');
  });
});

describe('BottomNav', () => {
  it('calls onSelect and marks active section', () => {
    const onSelect = vi.fn();
    render(<BottomNav activeId="analytics" onSelect={onSelect} />);

    expect(screen.getByRole('button', {name: 'Analytics'})).toHaveAttribute('aria-current', 'page');

    fireEvent.click(screen.getByRole('button', {name: 'Transfers'}));
    expect(onSelect).toHaveBeenCalledWith('transfers');
  });

  it('uses shortLabel for Logs & Terminal section with full label as title', () => {
    render(<BottomNav activeId="transfers" onSelect={vi.fn()} />);
    const button = screen.getByRole('button', {name: 'System'});
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('title', 'Logs & Terminal');
  });
});
