import {describe, expect, it} from 'vitest';
import {formatBytes, formatETA, formatSpeed, quotaBarWidthPct, quotaPercent} from './format';

describe('format helpers', () => {
  it('quotaPercent and quotaBarWidthPct guard bad input', () => {
    expect(quotaPercent(NaN, 100)).toBe(0);
    expect(quotaPercent(50, 100)).toBe(50);
    expect(quotaBarWidthPct(10, 0)).toBe(0);
    expect(quotaBarWidthPct(25, 100)).toBe(25);
  });

  it('formatBytes handles zero and scaling', () => {
    expect(formatBytes(0)).toBe('0 Bytes');
    expect(formatBytes(1536, 0)).toMatch(/KB$/);
  });

  it('formatETA formats hours minutes seconds', () => {
    expect(formatETA(-3)).toBe('--');
    expect(formatETA(0)).toBe('0s');
    expect(formatETA(45)).toContain('45');
    expect(formatETA(3665)).toMatch(/1h/);
  });

  it('formatSpeed uses bytes per second', () => {
    expect(formatSpeed(1024)).toContain('/s');
  });
});
