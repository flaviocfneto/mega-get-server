import { render, screen } from '@testing-library/react';
import type { FormEvent } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { DownloadSection } from './DownloadSection';

const noop = () => {};

function baseProps() {
  return {
    url: '',
    onUrlChange: noop,
    searchQuery: '',
    onSearchQueryChange: noop,
    newDownloadTags: '',
    onNewDownloadTagsChange: noop,
    newDownloadPriority: 'NORMAL' as const,
    onNewDownloadPriorityChange: noop as (v: 'LOW' | 'NORMAL' | 'HIGH') => void,
    onSubmit: (e: FormEvent) => {
      e.preventDefault();
    },
    onAddToQueue: noop,
    isDownloadSubmitting: false,
    lastDownloadStatus: null,
    onRetryLast: noop,
    downloadTelemetry: {
      clicks: 0,
      lastFiredAt: null,
      lastOutcome: 'idle' as const,
      lastUrlLength: 0,
      lastHttpStatus: null,
      lastErrorMessage: null as string | null,
      lastWasOverride: false,
    },
    telemetryUiEnabled: false,
    showDownloadTelemetry: false,
    onToggleDownloadTelemetry: noop,
  };
}

describe('DownloadSection', () => {
  it('renders Add to queue control', () => {
    render(<DownloadSection {...baseProps()} />);
    expect(screen.getByRole('button', { name: /add to queue/i })).toBeInTheDocument();
  });

  it('renders hostile lastDownloadStatus.message as text (no HTML injection)', () => {
    const hostile =
      '<img src=x onerror="window.__downloadSectionXss=1"><script>window.__downloadSectionXss=1</script>';

    render(
      <DownloadSection
        {...baseProps()}
        lastDownloadStatus={{
          phase: 'failed',
          message: hostile,
          url: '',
          updatedAt: 0,
        }}
      />,
    );

    const messageEl = screen.getByText(hostile, { exact: true });
    expect(messageEl).toBeInTheDocument();
    const block = messageEl.closest('div.mb-4');
    expect(block).not.toBeNull();
    expect(block!.querySelector('img')).toBeNull();
    expect(block!.querySelector('script')).toBeNull();
    expect((window as unknown as { __downloadSectionXss?: number }).__downloadSectionXss).toBeUndefined();
  });

  it('renders hostile downloadTelemetry.lastErrorMessage as text when telemetry is visible', () => {
    const hostile = '"><svg/onload=alert(1)';

    render(
      <DownloadSection
        {...baseProps()}
        telemetryUiEnabled
        showDownloadTelemetry
        downloadTelemetry={{
          ...baseProps().downloadTelemetry,
          lastErrorMessage: hostile,
        }}
      />,
    );

    const line = screen.getByText((content) => content.includes('last_error=') && content.includes(hostile));
    expect(line).toBeInTheDocument();
    expect(line.querySelector('svg')).toBeNull();
  });

  it('invokes onRetryLast when Retry is clicked for failed status', () => {
    const onRetryLast = vi.fn();
    render(
      <DownloadSection
        {...baseProps()}
        onRetryLast={onRetryLast}
        lastDownloadStatus={{
          phase: 'failed',
          message: 'err',
          url: '',
          updatedAt: 0,
        }}
      />,
    );
    screen.getByRole('button', { name: /retry/i }).click();
    expect(onRetryLast).toHaveBeenCalledTimes(1);
  });
});
