import { describe, expect, it } from 'vitest';
import {
  DEFAULT_APP_CONFIG,
  mergeAppConfig,
  normalizeAnalytics,
  normalizeHistory,
  normalizeLogs,
  normalizeToolDiagnostics,
  normalizeTransfers,
  normalizeLoginPostResponse,
  normalizeTerminalPostResponse,
  normalizeDownloadPostResponse,
  normalizeBulkPostResponse,
  normalizeSpeedLimitPostResponse,
  normalizePendingQueueItem,
  normalizePendingQueueList,
} from './apiNormalize';

describe('apiNormalize', () => {
  it('merges app config over defaults', () => {
    const merged = mergeAppConfig({
      transfer_limit: 3,
      download_dir: '/tmp/downloads',
      sound_alerts_enabled: false,
    });

    expect(merged.transfer_limit).toBe(3);
    expect(merged.download_dir).toBe('/tmp/downloads');
    expect(merged.sound_alerts_enabled).toBe(false);
    expect(merged.history_limit).toBe(DEFAULT_APP_CONFIG.history_limit);
  });

  it('normalizes legacy history string array', () => {
    const rows = normalizeHistory(['https://mega.nz/f1', 'https://mega.nz/f2']);
    expect(rows).toHaveLength(2);
    expect(rows[0].url).toBe('https://mega.nz/f1');
    expect(rows[0].timestamp).toBe(new Date(0).toISOString());
  });

  it('returns empty history for non-array payload', () => {
    expect(normalizeHistory({})).toEqual([]);
    expect(normalizeHistory(null)).toEqual([]);
  });

  it('sanitizes malformed structured history entries', () => {
    const rows = normalizeHistory([{ url: 'https://mega.nz/good', timestamp: '2026-01-01T00:00:00Z' }, { url: 123 }, null]);
    expect(rows).toEqual([{ url: 'https://mega.nz/good', timestamp: '2026-01-01T00:00:00Z' }]);
  });

  it('normalizes legacy log strings into log entries', () => {
    const logs = normalizeLogs(['hello', 'world']);
    expect(logs).toHaveLength(2);
    expect(logs[0].message).toBe('hello');
    expect(logs[0].level).toBe('INFO');
    expect(logs[0].category).toBe('SYSTEM');
  });

  it('passes through structured history and logs', () => {
    const history = [{ url: 'x', timestamp: '2025-01-01T00:00:00Z' }];
    const logs = [{ timestamp: '2025-01-01T00:00:00Z', level: 'ERROR', category: 'SYSTEM', message: 'boom' }];

    expect(normalizeHistory(history)).toEqual(history);
    expect(normalizeLogs(logs)).toEqual(logs);
  });

  it('normalizes malformed analytics payloads with defaults', () => {
    const out = normalizeAnalytics({
      total_downloaded_bytes: 'bad',
      average_speed_bps: 42,
      daily_stats: [{ date: '2026-04-01', bytes: 'x', count: 2 }],
    });
    expect(out.total_downloaded_bytes).toBe(0);
    expect(out.average_speed_bps).toBe(42);
    expect(out.daily_stats[0]).toEqual({ date: '2026-04-01', bytes: 0, count: 2 });
  });

  it('normalizes diagnostics payload safely', () => {
    const out = normalizeToolDiagnostics({
      ok: true,
      missing_tools: ['mega-cmd', 123],
      tools: [{ name: 'mega-cmd', available: true }, { bad: true }],
    });
    expect(out.ok).toBe(true);
    expect(out.missing_tools).toEqual(['mega-cmd']);
    expect(out.tools[0]).toMatchObject({ name: 'mega-cmd', available: true });
  });

  it('returns empty transfers for non-array payloads', () => {
    expect(normalizeTransfers(null)).toEqual([]);
    expect(normalizeTransfers({ tag: 'x' })).toEqual([]);
  });

  it('normalizes login POST payloads from unknown shapes', () => {
    expect(normalizeLoginPostResponse(null).status).toBe('error');
    const ok = normalizeLoginPostResponse({
      status: 'success',
      message: 'ok',
      account: { is_logged_in: true, email: 'a@b.co', account_type: 'FREE' },
    });
    expect(ok.status).toBe('success');
    expect(ok.account?.email).toBe('a@b.co');
  });

  it('normalizes terminal POST payloads with defaults', () => {
    const t = normalizeTerminalPostResponse({ ok: true, output: 'hi', exit_code: 0 });
    expect(t).toEqual({ ok: true, output: 'hi', exit_code: 0, blocked_reason: undefined });
    expect(normalizeTerminalPostResponse('garbage')).toEqual({
      ok: false,
      output: '',
      blocked_reason: undefined,
      exit_code: undefined,
    });
  });

  it('normalizes download and bulk POST payloads', () => {
    expect(normalizeDownloadPostResponse({ success: true, message: 'submitted' }).message).toBe('submitted');
    expect(normalizeBulkPostResponse({ affectedCount: 3 }).affectedCount).toBe(3);
    expect(normalizeSpeedLimitPostResponse({ message: 'saved', applied_to_megacmd: false }).applied_to_megacmd).toBe(
      false,
    );
  });

  it('normalizes pending queue list and download queued payload', () => {
    const row = normalizePendingQueueItem({
      id: '550e8400-e29b-41d4-a716-446655440000',
      url: 'https://mega.nz/file/x',
      tags: ['a'],
      priority: 'HIGH',
      created_at: '2020-01-01T00:00:00+00:00',
      status: 'PENDING',
      last_error: null,
    });
    expect(row?.priority).toBe('HIGH');
    expect(normalizePendingQueueList([{ id: '550e8400-e29b-41d4-a716-446655440000', url: 'https://mega.nz/f' }])).toHaveLength(1);
    const dl = normalizeDownloadPostResponse({
      success: true,
      message: 'Added to queue.',
      queued: true,
      item: row,
    });
    expect(dl.queued).toBe(true);
    expect(dl.item?.id).toBe('550e8400-e29b-41d4-a716-446655440000');
  });
});
