import {render, screen, waitFor} from '@testing-library/react';
import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest';
import {TransfersSessionProvider, useTransfersSession} from './TransfersSessionContext';

function jsonResponse(body: unknown) {
  return Promise.resolve({
    ok: true,
    status: 200,
    headers: {
      get: (k: string) => (String(k).toLowerCase() === 'content-type' ? 'application/json' : null),
    },
    json: async () => body,
  });
}

function Consumer() {
  const {transfers, pendingQueue} = useTransfersSession();
  return (
    <>
      <span data-testid="tc">{transfers.length}</span>
      <span data-testid="qc">{pendingQueue.length}</span>
    </>
  );
}

describe('TransfersSessionProvider', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
        if (url.includes('/api/transfers')) {
          return jsonResponse([
            {
              tag: 't1',
              url: 'https://mega.nz/x',
              progress_pct: 10,
              downloaded_bytes: 1,
              speed_bps: 2,
              state: 'ACTIVE',
              path: '/p',
              filename: 'f',
              size_bytes: 100,
              driver: 'megacmd',
            },
          ]);
        }
        if (url.includes('/api/queue')) {
          return jsonResponse([
            {
              id: '00000000-0000-4000-8000-000000000001',
              url: 'https://example.com/z',
              tags: [],
              priority: 'LOW',
              created_at: '2026-01-01T00:00:00Z',
              status: 'PENDING',
              last_error: null,
            },
          ]);
        }
        return jsonResponse({});
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('hydrates transfers and queue from API', async () => {
    render(
      <TransfersSessionProvider>
        <Consumer />
      </TransfersSessionProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('tc').textContent).toBe('1'));
    await waitFor(() => expect(screen.getByTestId('qc').textContent).toBe('1'));
  });
});
