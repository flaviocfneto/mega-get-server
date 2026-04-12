import {afterEach, describe, expect, it, vi} from 'vitest';
import {copyToClipboard} from './clipboard';

describe('copyToClipboard', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('writes text with navigator.clipboard', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal('navigator', {clipboard: {writeText}});
    await copyToClipboard('hello');
    expect(writeText).toHaveBeenCalledWith('hello');
  });

  it('does not throw when clipboard rejects', async () => {
    const writeText = vi.fn().mockRejectedValue(new Error('denied'));
    vi.stubGlobal('navigator', {clipboard: {writeText}});
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    await expect(copyToClipboard('x')).resolves.toBeUndefined();
    spy.mockRestore();
  });
});
