import type {Page} from '@playwright/test';

const defaultAnalytics = {
  total_downloaded_bytes: 0,
  total_transfers_completed: 0,
  total_transfers_failed: 0,
  average_speed_bps: 0,
  peak_speed_bps: 0,
  uptime_seconds: 1,
  daily_stats: [] as {day?: string; bytes?: number; count?: number}[],
  active_count: 0,
  queued_count: 0,
};

/**
 * Intercept relative `/api/*` calls from the preview SPA so E2E runs without a backend.
 */
export async function installApiMocks(page: Page, options?: {downloadShouldFail?: boolean}) {
  const failDownload = options?.downloadShouldFail ?? false;
  /** In-memory queue so GET /api/queue reflects POST /api/queue (SPA refetches after add). */
  const queueList: Record<string, unknown>[] = [];

  await page.route('**/api/**', async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const path = url.pathname;
    const method = req.method();

    const json = (body: unknown, status = 200) =>
      route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(body),
      });

    if (path === '/api/config' && method === 'GET') {
      return json({download_dir: '/data', transfer_limit: 2});
    }
    if (path === '/api/history' && method === 'GET') {
      return json([]);
    }
    if (path === '/api/logs' && method === 'GET') {
      return json([]);
    }
    if (path === '/api/account' && method === 'GET') {
      return json({is_logged_in: false, account_type: 'UNKNOWN', email: null});
    }
    if (path === '/api/analytics' && method === 'GET') {
      return json(defaultAnalytics);
    }
    if (path === '/api/diag/tools' && method === 'GET') {
      return json({ok: true, missing_tools: [], tools: []});
    }
    if (path === '/api/transfers' && method === 'GET') {
      return json([]);
    }
    if (path === '/api/queue' && method === 'GET') {
      return json(queueList);
    }
    if (path === '/api/queue' && method === 'POST') {
      let body: {url?: string; tags?: string[]; priority?: string} = {};
      try {
        body = (route.request().postDataJSON() as typeof body) ?? {};
      } catch {
        body = {};
      }
      const item = {
        id: '00000000-0000-4000-8000-000000000001',
        url: typeof body.url === 'string' ? body.url : 'https://mega.nz/file/mock',
        tags: Array.isArray(body.tags) ? body.tags : [],
        priority: typeof body.priority === 'string' ? body.priority : 'NORMAL',
        created_at: new Date().toISOString(),
        status: 'PENDING',
        last_error: null,
      };
      queueList.length = 0;
      queueList.push(item);
      return json({success: true, item});
    }
    if (path.startsWith('/api/queue/') && path.endsWith('/start') && method === 'POST') {
      return json({success: true, started: true, item: {}});
    }
    if (path === '/api/queue/start-next' && method === 'POST') {
      return json({success: true, started: false});
    }
    if (path === '/api/queue/start-all' && method === 'POST') {
      return json({success: true, startedIds: [], count: 0});
    }
    if (path.startsWith('/api/queue/') && method === 'DELETE') {
      const id = decodeURIComponent(path.slice('/api/queue/'.length));
      const idx = queueList.findIndex((q) => (q as {id?: string}).id === id);
      if (idx >= 0) queueList.splice(idx, 1);
      return json({success: true});
    }
    if (path === '/api/download' && method === 'POST') {
      if (failDownload) {
        return json({detail: 'Bad request'}, 400);
      }
      return json({success: true, message: 'Download command submitted.'});
    }
    if (path === '/api/login' && method === 'POST') {
      return json({status: 'success', message: 'Logged in.'});
    }
    if (path === '/api/logout' && method === 'POST') {
      return json({status: 'success', message: 'Logged out.'});
    }
    if (path === '/api/transfers/cancel-all' && method === 'POST') {
      return json({success: true});
    }
    if (path === '/api/history' && method === 'DELETE') {
      return json({success: true});
    }
    if (path === '/api/logs' && method === 'DELETE') {
      return json({success: true});
    }
    if (path === '/api/terminal' && method === 'POST') {
      let command = '';
      try {
        const raw = route.request().postDataJSON() as {command?: string} | null;
        command = typeof raw?.command === 'string' ? raw.command : '';
      } catch {
        command = '';
      }
      return json({ok: true, output: `ok:${command}`, exit_code: 0});
    }

    return json({});
  });
}
