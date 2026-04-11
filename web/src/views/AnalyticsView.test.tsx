import {render, screen} from '@testing-library/react';
import {describe, expect, it} from 'vitest';
import {AnalyticsView} from './AnalyticsView';

const sampleAnalytics = {
  total_downloaded_bytes: 1024,
  total_transfers_completed: 2,
  total_transfers_failed: 1,
  average_speed_bps: 1000,
  uptime_seconds: 3600,
  daily_stats: [{date: '2025-01-01', bytes: 100, count: 1}],
};

describe('AnalyticsView', () => {
  it('renders zeroed KPIs when analytics is null', () => {
    render(<AnalyticsView analytics={null} />);
    expect(screen.getByText('Total downloaded')).toBeInTheDocument();
    expect(screen.getByText('0 Bytes')).toBeInTheDocument();
  });

  it('renders KPI values when analytics is provided', () => {
    render(<AnalyticsView analytics={sampleAnalytics} />);
    expect(screen.getByText('1 KB')).toBeInTheDocument();
    expect(screen.getAllByText('2').length).toBeGreaterThan(0);
    expect(screen.getAllByText('1').length).toBeGreaterThan(0);
  });
});
