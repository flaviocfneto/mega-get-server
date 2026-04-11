import {render, screen} from '@testing-library/react';
import {describe, expect, it, vi} from 'vitest';
import {ToolDiagnosticsPanel} from './ToolDiagnosticsPanel';

describe('ToolDiagnosticsPanel', () => {
  it('renders without crashing when tools and missing_tools are missing', () => {
    const report = {ok: true} as any;
    render(
      <ToolDiagnosticsPanel
        report={report}
        loading={false}
        onRefresh={() => {}}
        onInstallCommand={() => {}}
      />,
    );
    expect(screen.getByText('Tool diagnostics')).toBeInTheDocument();
    expect(screen.getByRole('button', {name: /refresh/i})).toBeInTheDocument();
  });

  it('does not throw when ok is false but tools and missing_tools are absent', () => {
    const report = {ok: false} as any;
    render(
      <ToolDiagnosticsPanel
        report={report}
        loading={false}
        onRefresh={() => {}}
        onInstallCommand={() => {}}
      />,
    );
    expect(screen.getByText(/0 missing/i)).toBeInTheDocument();
  });

  it('renders tool rows when tools is populated', () => {
    render(
      <ToolDiagnosticsPanel
        report={{
          ok: false,
          missing_tools: ['megacmd'],
          tools: [{name: 'megacmd', available: false, required_for: ['downloads']}],
        }}
        loading={false}
        onRefresh={vi.fn()}
        onInstallCommand={vi.fn()}
      />,
    );
    expect(screen.getByText('megacmd')).toBeInTheDocument();
    expect(screen.getByText(/1 missing/i)).toBeInTheDocument();
  });
});
