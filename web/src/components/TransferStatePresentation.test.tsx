import {render} from '@testing-library/react';
import {describe, expect, it} from 'vitest';
import {TransferStateIcon, transferStateBadgeClassName} from './TransferStatePresentation';

describe('TransferStatePresentation', () => {
  it('maps known states to badge classes', () => {
    expect(transferStateBadgeClassName('ACTIVE')).toContain('ft-brand-teal');
    expect(transferStateBadgeClassName('WEIRD')).toContain('ft-border');
  });

  it('renders icons for transfer states', () => {
    const {rerender, container} = render(<TransferStateIcon state="ACTIVE" />);
    expect(container.querySelector('.animate-spin')).toBeTruthy();
    rerender(<TransferStateIcon state="COMPLETED" />);
    expect(container.querySelector('svg')).toBeTruthy();
    rerender(<TransferStateIcon state="WEIRD" />);
    expect(container.firstChild).toBeNull();
  });
});
