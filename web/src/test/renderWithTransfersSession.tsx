import type {ReactElement, ReactNode} from 'react';
import {render, type RenderOptions} from '@testing-library/react';
import {TransfersSessionProvider} from '../context/TransfersSessionContext';

/** Wrap tree with the same provider used in `main.tsx` (and `App.test.tsx` via `renderApp`). */
export function renderWithTransfersSession(ui: ReactElement, options?: RenderOptions) {
  function Wrapper({children}: {children: ReactNode}) {
    return <TransfersSessionProvider>{children}</TransfersSessionProvider>;
  }
  return render(ui, {wrapper: Wrapper, ...options});
}
