import {AlertCircle, CheckCircle2, Command} from 'lucide-react';
import type {ToolDiagnosticsReport} from '../types';
import {copyToClipboard} from '../lib/clipboard';
import {ftBtnPrimarySm, ftFocusRing} from '../lib/ftUi';

type Props = {
  report: ToolDiagnosticsReport;
  loading: boolean;
  onRefresh: () => void;
  onInstallCommand: (cmd: string) => void;
};

export function ToolDiagnosticsPanel({report, loading, onRefresh, onInstallCommand}: Props) {
  const tools = Array.isArray(report.tools) ? report.tools : [];
  const missingCount = Array.isArray(report.missing_tools) ? report.missing_tools.length : 0;

  return (
    <section
      className="mb-6 rounded-2xl border border-[var(--ft-border)] bg-[var(--card)] p-4 shadow-sm"
      aria-labelledby="tool-diagnostics-heading"
    >
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Command className="h-4 w-4 text-[var(--ft-warning)]" aria-hidden />
          <h2 id="tool-diagnostics-heading" className="text-sm font-bold text-[var(--foreground)]">
            Tool diagnostics
          </h2>
          {!report.ok && (
            <span className="rounded-full border border-[var(--ft-warning)]/40 bg-[var(--ft-warning-bg)] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[var(--ft-warning)]">
              {missingCount} missing
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={onRefresh}
          className={`rounded-lg border border-[var(--ft-border)] px-2 py-1 text-[11px] font-bold text-[var(--foreground)] hover:bg-[var(--muted)] ${ftFocusRing}`}
        >
          Refresh
        </button>
      </div>

      {loading && (
        <p className="mb-2 text-xs text-[var(--muted-foreground)]">Refreshing diagnostics…</p>
      )}

      <ul className="space-y-3">
        {tools.map((tool) => (
          <li
            key={tool.name}
            className="rounded-xl border border-[var(--ft-border)] bg-[var(--muted)]/30 p-3"
          >
            <div className="mb-1 flex flex-wrap items-center gap-2">
              {tool.available ? (
                <CheckCircle2 className="h-4 w-4 text-[var(--ft-success)]" aria-hidden />
              ) : (
                <AlertCircle className="h-4 w-4 text-[var(--ft-danger)]" aria-hidden />
              )}
              <span className="text-sm font-bold text-[var(--foreground)]">{tool.name}</span>
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${
                  tool.available
                    ? 'border border-[var(--ft-success)]/35 bg-[var(--ft-success-bg)] text-[var(--ft-success)]'
                    : 'border border-[var(--ft-danger)]/35 bg-[var(--ft-danger-bg)] text-[var(--ft-danger)]'
                }`}
              >
                {tool.available ? 'Available' : 'Missing'}
              </span>
            </div>

            {!!tool.required_for?.length && (
              <p className="text-xs text-[var(--muted-foreground)]">
                <span className="font-semibold text-[var(--foreground)]">Why it matters:</span>{' '}
                Required for {tool.required_for.join(', ')}.
              </p>
            )}

            {!!tool.install_instructions && (
              <p className="mt-1 text-xs text-[var(--muted-foreground)]">{tool.install_instructions}</p>
            )}

            {!tool.available && !!tool.suggested_install_commands?.length && (
              <div className="mt-3 space-y-2">
                <p className="text-[11px] font-bold uppercase tracking-wide text-[var(--muted-foreground)]">
                  Run this
                </p>
                {tool.suggested_install_commands.map((cmd) => (
                  <div
                    key={`${tool.name}-${cmd}`}
                    className="rounded-lg border border-[var(--ft-border)] bg-[var(--background)] p-2"
                  >
                    <code className="block overflow-x-auto font-mono text-[11px] text-[var(--foreground)]">
                      {cmd}
                    </code>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <button
                        type="button"
                        onClick={() => onInstallCommand(cmd)}
                        className={`${ftBtnPrimarySm} ${ftFocusRing}`}
                      >
                        Copy install command
                      </button>
                      <button
                        type="button"
                        onClick={() => void copyToClipboard(cmd)}
                        className={`rounded-md border border-[var(--ft-border)] px-2 py-1 text-[10px] font-bold hover:bg-[var(--muted)] ${ftFocusRing}`}
                      >
                        Copy only
                      </button>
                    </div>
                    <p className="mt-2 text-[10px] text-[var(--muted-foreground)]">
                      Expected: tool becomes available after install; use Refresh to re-check.
                    </p>
                  </div>
                ))}
              </div>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
