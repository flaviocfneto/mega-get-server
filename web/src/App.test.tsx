import type {ReactElement} from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';
import { TransfersSessionProvider } from './context/TransfersSessionContext';

function renderApp(ui: ReactElement = <App />) {
  return render(<TransfersSessionProvider>{ui}</TransfersSessionProvider>);
}

function mockJsonResponse(payload: unknown, ok = true, status = 200) {
  return Promise.resolve({
    ok,
    status,
    headers: {
      get: (name: string) => (name.toLowerCase() === 'content-type' ? 'application/json' : null),
    },
    json: async () => payload,
  } as Response);
}

describe('App', () => {
  beforeEach(() => {
    window.history.replaceState(null, '', '/');
    vi.restoreAllMocks();
    window.localStorage.clear();
    vi.spyOn(globalThis, 'setInterval').mockImplementation(() => 0 as any);
    vi.spyOn(globalThis, 'clearInterval').mockImplementation(() => {});
    let isLoggedIn = false;

    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString();
      const method = init?.method ?? 'GET';

      if (url === '/api/config' && method === 'GET') {
        return mockJsonResponse({ download_dir: '/data', transfer_limit: 2 });
      }
      if (url === '/api/history' && method === 'GET') {
        return mockJsonResponse([]);
      }
      if (url === '/api/logs' && method === 'GET') {
        return mockJsonResponse([]);
      }
      if (url === '/api/account' && method === 'GET') {
        return mockJsonResponse({ is_logged_in: isLoggedIn, account_type: isLoggedIn ? 'FREE' : 'UNKNOWN', email: isLoggedIn ? 'user@example.com' : null });
      }
      if (url === '/api/analytics' && method === 'GET') {
        return mockJsonResponse({
          total_downloaded_bytes: 0,
          total_transfers_completed: 0,
          total_transfers_failed: 0,
          average_speed_bps: 0,
          peak_speed_bps: 0,
          uptime_seconds: 1,
          daily_stats: [],
          active_count: 0,
          queued_count: 0,
        });
      }
      if (url === '/api/diag/tools' && method === 'GET') {
        return mockJsonResponse({ ok: true, missing_tools: [], tools: [] });
      }
      if (url === '/api/transfers' && method === 'GET') {
        return mockJsonResponse([]);
      }
      if (url === '/api/download' && method === 'POST') {
        return mockJsonResponse({ success: true, message: 'Download command submitted.' }, true, 200);
      }
      if (url === '/api/login' && method === 'POST') {
        isLoggedIn = true;
        return mockJsonResponse({ status: 'success', message: 'Logged in.' });
      }
      if (url === '/api/logout' && method === 'POST') {
        isLoggedIn = false;
        return mockJsonResponse({ status: 'success', message: 'Logged out.' });
      }
      if (url === '/api/transfers/cancel-all' && method === 'POST') {
        return mockJsonResponse({ success: true });
      }
      if (url === '/api/history' && method === 'DELETE') {
        return mockJsonResponse({ success: true });
      }
      if (url === '/api/logs' && method === 'DELETE') {
        return mockJsonResponse({ success: true });
      }
      if (url === '/api/terminal' && method === 'POST') {
        const body = init?.body ? (JSON.parse(String(init.body)) as {command?: string}) : {};
        const command = typeof body.command === 'string' ? body.command : '';
        return mockJsonResponse({ok: true, output: `out:${command}`, exit_code: 0});
      }
      return mockJsonResponse({}, true, 200);
    });

    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
  });

  it('renders primary download form and starts with disabled submit', async () => {
    renderApp();
    expect(await screen.findByPlaceholderText(/Paste MEGA\.nz export link here/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Download' })).toBeDisabled();
  });

  it('submits a download URL and shows submitted status', async () => {
    renderApp();

    const urlInput = await screen.findByPlaceholderText(/Paste MEGA\.nz export link here/);
    fireEvent.change(urlInput, { target: { value: 'https://mega.nz/file/abc' } });
    fireEvent.click(screen.getByRole('button', { name: 'Download' }));

    await waitFor(() => {
      expect(screen.getByText(/Last download:\s*submitted/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Download command submitted/i).length).toBeGreaterThan(0);
    });
  });

  it('opens login modal and performs login flow', async () => {
    renderApp();
    fireEvent.click(
      await screen.findByRole('button', {name: /Log in to MEGA/i, hidden: true}),
    );
    expect(await screen.findByPlaceholderText('your@email.com')).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText('your@email.com'), { target: { value: 'user@example.com' } });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'secret' } });
    fireEvent.click(screen.getAllByRole('button', { name: /^Login$/i })[0]);
    await waitFor(() => {
      expect(screen.getByText(/Logged in/i)).toBeInTheDocument();
    });
  });

  it('switches tabs between history and analytics', async () => {
    renderApp();
    fireEvent.click((await screen.findAllByRole('button', {name: 'History and Queue'}))[0]);
    expect(await screen.findByPlaceholderText(/Search history/)).toBeInTheDocument();

    fireEvent.click((await screen.findAllByRole('button', {name: 'Analytics'}))[0]);
    expect(await screen.findByText(/Total Downloaded/i)).toBeInTheDocument();
    expect(await screen.findByText(/Average speed/i)).toBeInTheDocument();
  });

  it('opens settings modal and shows Advanced Settings and General sections', async () => {
    renderApp();
    await screen.findByPlaceholderText(/Paste MEGA\.nz export link here/);
    fireEvent.click(screen.getByTitle('Settings'));
    expect(await screen.findByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Advanced Settings')).toBeInTheDocument();
    expect(screen.getByText('General')).toBeInTheDocument();
    expect(screen.getByText('Download Directory')).toBeInTheDocument();
    expect(screen.getByText('Save Changes')).toBeInTheDocument();
  });

  it('toggles download telemetry debug details', async () => {
    renderApp();
    await screen.findByPlaceholderText(/Paste MEGA\.nz export link here/);

    expect(screen.getByText('Download telemetry (debug)')).toBeInTheDocument();
    expect(screen.queryByText(/http_status=/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', {name: 'Show'}));
    expect(await screen.findByText(/http_status=n\/a/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', {name: 'Hide'}));
    await waitFor(() => {
      expect(screen.queryByText(/http_status=/i)).not.toBeInTheDocument();
    });
  });

  it('persists telemetry visibility across remounts', async () => {
    const {unmount} = renderApp();
    await screen.findByPlaceholderText(/Paste MEGA\.nz export link here/);
    fireEvent.click(screen.getByRole('button', {name: 'Show'}));
    expect(await screen.findByText(/http_status=n\/a/i)).toBeInTheDocument();
    unmount();

    renderApp();
    await screen.findByPlaceholderText(/Paste MEGA\.nz export link here/);
    expect(await screen.findByText(/http_status=n\/a/i)).toBeInTheDocument();
    expect(screen.getByRole('button', {name: 'Hide'})).toBeInTheDocument();
  });

  it(
    'can fully hide telemetry panel from Advanced Settings',
    async () => {
      renderApp();
      await screen.findByPlaceholderText(/Paste MEGA\.nz export link here/);
      expect(screen.getByText('Download telemetry (debug)')).toBeInTheDocument();

      fireEvent.click(screen.getByTitle('Settings'));
      expect(await screen.findByRole('dialog')).toBeInTheDocument();
      fireEvent.click(screen.getByLabelText('Toggle download debug telemetry'));
      fireEvent.click(screen.getByRole('button', {name: 'Cancel'}));

      await waitFor(
        () => {
          expect(screen.queryByText('Download telemetry (debug)')).not.toBeInTheDocument();
        },
        {timeout: 10000},
      );
      expect(screen.queryByRole('button', {name: /show/i})).not.toBeInTheDocument();
    },
    15000,
  );

  it('falls back safely when telemetry localStorage values are corrupted', async () => {
    window.localStorage.setItem('ft_download_telemetry_visible', 'garbage');
    window.localStorage.setItem('ft_download_telemetry_ui_enabled', 'garbage');
    renderApp();
    await screen.findByPlaceholderText(/Paste MEGA\.nz export link here/);
    expect(screen.getByText('Download telemetry (debug)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Show' })).toBeInTheDocument();
    expect(screen.queryByText(/http_status=/i)).not.toBeInTheDocument();
  });

  it('surfaces API detail envelope on failed download', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString();
      const method = init?.method ?? 'GET';
      if (url === '/api/download' && method === 'POST') {
        return mockJsonResponse({ detail: 'Invalid payload from backend' }, false, 400);
      }
      if (url === '/api/config' && method === 'GET') return mockJsonResponse({ download_dir: '/data', transfer_limit: 2 });
      if (url === '/api/history' && method === 'GET') return mockJsonResponse([]);
      if (url === '/api/logs' && method === 'GET') return mockJsonResponse([]);
      if (url === '/api/account' && method === 'GET') return mockJsonResponse({ is_logged_in: false, account_type: 'UNKNOWN', email: null });
      if (url === '/api/analytics' && method === 'GET') return mockJsonResponse({ total_downloaded_bytes: 0, total_transfers_completed: 0, total_transfers_failed: 0, average_speed_bps: 0, uptime_seconds: 1, daily_stats: [] });
      if (url === '/api/diag/tools' && method === 'GET') return mockJsonResponse({ ok: true, missing_tools: [], tools: [] });
      if (url === '/api/transfers' && method === 'GET') return mockJsonResponse([]);
      return mockJsonResponse({});
    });
    vi.stubGlobal('fetch', fetchMock);
    renderApp();
    const urlInput = await screen.findByPlaceholderText(/Paste MEGA\.nz export link here/);
    fireEvent.change(urlInput, { target: { value: 'https://mega.nz/file/abc' } });
    fireEvent.click(screen.getByRole('button', { name: 'Download' }));
    expect((await screen.findAllByText('Invalid payload from backend')).length).toBeGreaterThan(0);
  });

  it('settings modal shows account storage when logged in', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString();
      const method = init?.method ?? 'GET';

      if (url === '/api/config' && method === 'GET') {
        return mockJsonResponse({ download_dir: '/data', transfer_limit: 2 });
      }
      if (url === '/api/history' && method === 'GET') {
        return mockJsonResponse([]);
      }
      if (url === '/api/logs' && method === 'GET') {
        return mockJsonResponse([]);
      }
      if (url === '/api/account' && method === 'GET') {
        return mockJsonResponse({
          is_logged_in: true,
          account_type: 'FREE',
          email: 'user@example.com',
          storage_used_bytes: 1_000_000,
          storage_total_bytes: 10_000_000,
          bandwidth_used_bytes: 500_000,
          bandwidth_limit_bytes: 5_000_000,
        });
      }
      if (url === '/api/analytics' && method === 'GET') {
        return mockJsonResponse({
          total_downloaded_bytes: 0,
          total_transfers_completed: 0,
          total_transfers_failed: 0,
          average_speed_bps: 0,
          peak_speed_bps: 0,
          uptime_seconds: 1,
          daily_stats: [],
          active_count: 0,
          queued_count: 0,
        });
      }
      if (url === '/api/diag/tools' && method === 'GET') {
        return mockJsonResponse({ ok: true, missing_tools: [], tools: [] });
      }
      if (url === '/api/transfers' && method === 'GET') {
        return mockJsonResponse([]);
      }
      if (url === '/api/download' && method === 'POST') {
        return mockJsonResponse({ success: true, message: 'Download command submitted.' }, true, 200);
      }
      if (url === '/api/login' && method === 'POST') {
        return mockJsonResponse({ status: 'success', message: 'Logged in.' });
      }
      if (url === '/api/logout' && method === 'POST') {
        return mockJsonResponse({ status: 'success', message: 'Logged out.' });
      }
      if (url === '/api/transfers/cancel-all' && method === 'POST') {
        return mockJsonResponse({ success: true });
      }
      if (url === '/api/history' && method === 'DELETE') {
        return mockJsonResponse({ success: true });
      }
      if (url === '/api/logs' && method === 'DELETE') {
        return mockJsonResponse({ success: true });
      }
      return mockJsonResponse({}, true, 200);
    });

    vi.stubGlobal('fetch', fetchMock);

    renderApp();
    await waitFor(() => {
      expect(screen.getByText('user@example.com')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTitle('Settings'));
    expect(await screen.findByRole('dialog')).toBeInTheDocument();
    expect(await screen.findByText('Storage Usage')).toBeInTheDocument();
  });

  it('hash deep link #/system/terminal opens MEGA Terminal input', async () => {
    window.location.hash = '#/system/terminal';
    renderApp();
    expect(await screen.findByPlaceholderText('Enter MEGAcmd command...')).toBeInTheDocument();
  });

  it(
    'terminal Typed only filter hides preset quick-action commands',
    async () => {
      renderApp();
      await screen.findByPlaceholderText(/Paste MEGA\.nz export link here/);
      fireEvent.click(screen.getByRole('button', {name: 'System'}));
      expect(await screen.findByRole('tab', {name: /MEGA Terminal/i})).toBeInTheDocument();
      fireEvent.click(screen.getByRole('tab', {name: /MEGA Terminal/i}));
      fireEvent.click(screen.getByRole('button', {name: /mega-whoami/i}));
      await waitFor(() => {
        expect(screen.getByText('out:mega-whoami')).toBeInTheDocument();
      });

      const input = screen.getByPlaceholderText('Enter MEGAcmd command...');
      fireEvent.change(input, {target: {value: 'mega-echo-test'}});
      const form = input.closest('form');
      expect(form).toBeTruthy();
      fireEvent.submit(form!);
      await waitFor(() => {
        expect(screen.getByText('out:mega-echo-test')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', {name: /Show only commands typed in the input line/i}));
      expect(screen.queryByText('out:mega-whoami')).not.toBeInTheDocument();
      expect(screen.getByText('out:mega-echo-test')).toBeInTheDocument();
    },
    20_000,
  );
});
