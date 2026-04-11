import { describe, expect, it, vi, afterEach } from 'vitest';
import { ApiError, apiDeleteResult, apiGet, apiPost, apiPostResult, isApiFailure } from './api';

function jsonResponse(body: unknown, init: { ok: boolean; status: number; contentType?: string }) {
  const headers = new Headers();
  headers.set('content-type', init.contentType ?? 'application/json');
  return {
    ok: init.ok,
    status: init.status,
    headers,
    json: async () => body,
  } as Response;
}

describe('api', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('apiGet returns unknown JSON on success', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(jsonResponse({ hello: 'world' }, { ok: true, status: 200 })),
    );
    const data = await apiGet('/api/x');
    expect(data).toEqual({ hello: 'world' });
  });

  it('apiGet throws ApiError with FastAPI detail on error JSON', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse({ detail: 'Only MEGA URLs are allowed' }, { ok: false, status: 400 }),
      ),
    );
    await expect(apiGet('/api/download')).rejects.toMatchObject({
      name: 'ApiError',
      status: 400,
      message: 'Only MEGA URLs are allowed',
      details: 'Only MEGA URLs are allowed',
    } satisfies Partial<ApiError>);
  });

  it('apiGet uses message field when present on error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse({ message: 'Bad', detail: 'Detail line' }, { ok: false, status: 422 }),
      ),
    );
    await expect(apiGet('/api/x')).rejects.toMatchObject({
      message: 'Bad',
      details: 'Detail line',
    });
  });

  it('apiPost returns unknown on success', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(jsonResponse({ success: true }, { ok: true, status: 200 })),
    );
    const data = await apiPost('/api/config', {});
    expect(data).toEqual({ success: true });
  });

  it('apiPostResult returns failure envelope from detail', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse({ detail: 'missing field' }, { ok: false, status: 400 }),
      ),
    );
    const r = await apiPostResult('/api/x', {});
    expect(isApiFailure(r)).toBe(true);
    if (isApiFailure(r)) {
      expect(r.status).toBe(400);
      expect(r.message).toBe('missing field');
    }
  });

  it('apiPostResult returns success with unknown data', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(jsonResponse({ status: 'ok' }, { ok: true, status: 200 })),
    );
    const r = await apiPostResult('/api/login', { email: 'a@b.co', password: 'x' });
    expect(r.ok).toBe(true);
    if (r.ok) {
      expect(r.data).toEqual({ status: 'ok' });
    }
  });

  it('apiPostResult handles fetch rejection', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network down')));
    const r = await apiPostResult('/api/x', {});
    expect(isApiFailure(r)).toBe(true);
    if (isApiFailure(r)) {
      expect(r.status).toBe(0);
      expect(r.message).toContain('Network request failed');
    }
  });

  it('apiDeleteResult returns success data as unknown', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(jsonResponse({ success: true }, { ok: true, status: 200 })),
    );
    const r = await apiDeleteResult('/api/history');
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.data).toEqual({ success: true });
  });
});
