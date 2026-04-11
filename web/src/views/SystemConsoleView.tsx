import React, {useMemo, useState} from 'react';
import {
  Activity,
  Copy,
  DownloadCloud,
  FileText,
  Filter,
  HardDrive,
  Keyboard,
  Send,
  ShieldCheck,
  Tag,
  Terminal,
  Timer,
  User,
  Zap,
} from 'lucide-react';
import type {AppConfig, LogCategory, LogEntry, LogLevel, TerminalHistoryEntry} from '../types';
import {copyToClipboard} from '../lib/clipboard';
import {ftFocusRing} from '../lib/ftUi';

export type SystemConsoleViewProps = {
  isTerminalOpen: boolean;
  setIsTerminalOpen: (value: boolean) => void;
  filteredLogs: LogEntry[];
  logFilterLevel: LogLevel | 'ALL';
  setLogFilterLevel: (v: LogLevel | 'ALL') => void;
  logFilterCategory: LogCategory | 'ALL';
  setLogFilterCategory: (v: LogCategory | 'ALL') => void;
  logSearchQuery: string;
  setLogSearchQuery: (v: string) => void;
  exportLogs: () => void;
  clearLogs: () => void | Promise<void>;
  terminalOutput: TerminalHistoryEntry[];
  terminalInput: string;
  setTerminalInput: (v: string) => void;
  executeCommand: (cmd?: string) => void | Promise<void>;
  clearTerminalOutput: () => void;
  terminalEndRef: React.RefObject<HTMLDivElement | null>;
  logEndRef: React.RefObject<HTMLDivElement | null>;
  config: AppConfig | null;
  updateConfig: (updates: Partial<AppConfig>) => void | Promise<void>;
};

/**
 * Combined server log + MEGAcmd terminal (one primary app section).
 */
export function SystemConsoleView({
  isTerminalOpen,
  setIsTerminalOpen,
  filteredLogs,
  logFilterLevel,
  setLogFilterLevel,
  logFilterCategory,
  setLogFilterCategory,
  logSearchQuery,
  setLogSearchQuery,
  exportLogs,
  clearLogs,
  terminalOutput,
  terminalInput,
  setTerminalInput,
  executeCommand,
  clearTerminalOutput,
  terminalEndRef,
  logEndRef,
  config,
  updateConfig,
}: SystemConsoleViewProps) {
  const [manualOnly, setManualOnly] = useState(false);

  const displayedTerminal = useMemo(() => {
    if (!manualOnly) return terminalOutput;
    return terminalOutput.filter((e) => (e.source ?? 'preset') === 'manual');
  }, [terminalOutput, manualOnly]);

  return (
    <div className="flex min-h-[min(70vh,calc(100vh-12rem))] flex-col rounded-2xl border border-[var(--ft-border)] bg-[var(--card)] shadow-sm">
      <div className="flex flex-col gap-3 border-b border-[var(--border)] bg-[var(--muted)]/20 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <div
          role="tablist"
          aria-label="System console mode"
          className="flex rounded-xl border border-[var(--ft-border)] bg-[var(--background)] p-1"
        >
          <button
            type="button"
            role="tab"
            aria-selected={!isTerminalOpen}
            className={`rounded-lg px-3 py-2 text-xs font-bold uppercase tracking-wider transition-colors ${ftFocusRing} ${
              !isTerminalOpen
                ? 'bg-[color-mix(in_srgb,var(--ft-accent)_16%,transparent)] text-[var(--ft-accent)]'
                : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
            }`}
            onClick={() => setIsTerminalOpen(false)}
          >
            <span className="flex items-center gap-2">
              <FileText className="h-4 w-4" aria-hidden />
              System log
            </span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={isTerminalOpen}
            className={`rounded-lg px-3 py-2 text-xs font-bold uppercase tracking-wider transition-colors ${ftFocusRing} ${
              isTerminalOpen
                ? 'bg-[color-mix(in_srgb,var(--ft-accent)_16%,transparent)] text-[var(--ft-accent)]'
                : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
            }`}
            onClick={() => setIsTerminalOpen(true)}
          >
            <span className="flex items-center gap-2">
              <Terminal className="h-4 w-4" aria-hidden />
              MEGA Terminal
            </span>
          </button>
        </div>

        {!isTerminalOpen ? (
          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            <div className="flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--background)] px-2 py-1">
              <Filter className="h-3 w-3 text-[var(--muted-foreground)]" aria-hidden />
              <select
                value={logFilterLevel}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === 'ALL' || value === 'INFO' || value === 'WARN' || value === 'ERROR' || value === 'SUCCESS') {
                    setLogFilterLevel(value);
                  }
                }}
                className="cursor-pointer bg-transparent text-[10px] font-bold uppercase text-[var(--muted-foreground)] focus:outline-none"
              >
                <option value="ALL">All Levels</option>
                <option value="INFO">Info</option>
                <option value="SUCCESS">Success</option>
                <option value="WARN">Warning</option>
                <option value="ERROR">Error</option>
              </select>
            </div>
            <div className="flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--background)] px-2 py-1">
              <Tag className="h-3 w-3 text-[var(--muted-foreground)]" aria-hidden />
              <select
                value={logFilterCategory}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === 'ALL' || value === 'SYSTEM' || value === 'TRANSFER' || value === 'AUTOMATION' || value === 'AUTH') {
                    setLogFilterCategory(value);
                  }
                }}
                className="cursor-pointer bg-transparent text-[10px] font-bold uppercase text-[var(--muted-foreground)] focus:outline-none"
              >
                <option value="ALL">All Categories</option>
                <option value="SYSTEM">System</option>
                <option value="TRANSFER">Transfer</option>
                <option value="AUTOMATION">Automation</option>
                <option value="AUTH">Auth</option>
              </select>
            </div>
            <input
              type="text"
              value={logSearchQuery}
              onChange={(e) => setLogSearchQuery(e.target.value)}
              placeholder="Search logs..."
              className={`w-full min-w-[8rem] max-w-[12rem] rounded-lg border border-[var(--ft-border)] bg-[var(--background)] px-3 py-1 text-[10px] focus:outline-none sm:w-32 ${ftFocusRing}`}
            />
            <button
              type="button"
              onClick={exportLogs}
              className="rounded p-1 text-[var(--muted-foreground)] transition-colors hover:bg-[var(--muted)] hover:text-[var(--ft-accent)]"
              title="Export Logs"
            >
              <FileText className="h-4 w-4" aria-hidden />
            </button>
            <button
              type="button"
              onClick={() => void clearLogs()}
              className="text-[10px] font-bold uppercase text-gray-500 transition-colors hover:text-rose-400"
            >
              Clear
            </button>
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-2">
            <div
              className="flex rounded-lg border border-[var(--ft-border)] bg-[var(--background)] p-0.5 text-[10px] font-bold"
              role="group"
              aria-label="Terminal history filter"
            >
              <button
                type="button"
                className={`rounded-md px-2 py-1 uppercase transition-colors ${ftFocusRing} ${
                  !manualOnly
                    ? 'bg-[color-mix(in_srgb,var(--ft-accent)_14%,transparent)] text-[var(--ft-accent)]'
                    : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
                }`}
                onClick={() => setManualOnly(false)}
              >
                All runs
              </button>
              <button
                type="button"
                aria-label="Show only commands typed in the input line"
                className={`rounded-md px-2 py-1 uppercase transition-colors ${ftFocusRing} ${
                  manualOnly
                    ? 'bg-[color-mix(in_srgb,var(--ft-accent)_14%,transparent)] text-[var(--ft-accent)]'
                    : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
                }`}
                onClick={() => setManualOnly(true)}
              >
                Typed only
              </button>
            </div>
            <button
              type="button"
              onClick={clearTerminalOutput}
              className="text-[10px] font-bold uppercase text-gray-500 transition-colors hover:text-rose-400"
            >
              Clear terminal
            </button>
          </div>
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-hidden" role="tabpanel">
        {isTerminalOpen ? (
          <div className="flex h-full min-h-[320px] flex-col p-4 font-mono text-[11px] bg-black/20">
            <div className="mb-4 flex flex-wrap gap-2 rounded-xl border border-white/10 bg-white/5 p-3">
              <button
                type="button"
                onClick={() => void executeCommand('mega-whoami')}
                className="flex items-center gap-1.5 rounded border border-[color-mix(in_srgb,var(--ft-accent)_35%,var(--ft-border))] bg-[color-mix(in_srgb,var(--ft-accent)_10%,transparent)] px-2 py-1 text-[var(--ft-accent)] transition-colors hover:bg-[color-mix(in_srgb,var(--ft-accent)_18%,transparent)]"
              >
                <User className="h-3 w-3" /> mega-whoami
              </button>
              <button
                type="button"
                onClick={() => void executeCommand('mega-ls')}
                className="flex items-center gap-1.5 rounded border border-emerald-500/20 bg-emerald-500/10 px-2 py-1 text-emerald-400 transition-colors hover:bg-emerald-500/20"
              >
                <Filter className="h-3 w-3" /> mega-ls
              </button>
              <button
                type="button"
                onClick={() => void executeCommand('mega-df')}
                className="flex items-center gap-1.5 rounded border border-purple-500/20 bg-purple-500/10 px-2 py-1 text-purple-400 transition-colors hover:bg-purple-500/20"
              >
                <HardDrive className="h-3 w-3" /> mega-df
              </button>
              <button
                type="button"
                onClick={() => void executeCommand('mega-export')}
                className="flex items-center gap-1.5 rounded border border-amber-500/20 bg-amber-500/10 px-2 py-1 text-amber-400 transition-colors hover:bg-amber-500/20"
              >
                <DownloadCloud className="h-3 w-3" /> mega-export
              </button>
              <button
                type="button"
                onClick={() => void executeCommand('mega-transfers')}
                className="flex items-center gap-1.5 rounded border border-cyan-500/20 bg-cyan-500/10 px-2 py-1 text-cyan-400 transition-colors hover:bg-cyan-500/20"
              >
                <Activity className="h-3 w-3" /> mega-transfers
              </button>
              <button
                type="button"
                onClick={() => void executeCommand('mega-log')}
                className="flex items-center gap-1.5 rounded border border-rose-500/20 bg-rose-500/10 px-2 py-1 text-rose-400 transition-colors hover:bg-rose-500/20"
              >
                <Zap className="h-3 w-3" /> mega-log
              </button>
              <div className="mx-1 h-6 w-px bg-white/10" />
              <button
                type="button"
                onClick={() => {
                  const newEnabled = !config?.is_scheduling_enabled;
                  void updateConfig({is_scheduling_enabled: newEnabled});
                  void executeCommand(`Scheduling ${newEnabled ? 'Enabled' : 'Disabled'}`);
                }}
                className={`flex items-center gap-1.5 rounded border px-2 py-1 transition-colors ${
                  config?.is_scheduling_enabled
                    ? 'border-amber-500/30 bg-amber-500/20 text-amber-400'
                    : 'border-white/10 bg-white/5 text-white/40'
                }`}
              >
                <Timer className="h-3 w-3" /> Toggle Schedule
              </button>
              <button
                type="button"
                onClick={() => {
                  const newPrivacy = !config?.is_privacy_mode;
                  void updateConfig({is_privacy_mode: newPrivacy});
                  void executeCommand(`Privacy Mode ${newPrivacy ? 'Enabled' : 'Disabled'}`);
                }}
                className={`flex items-center gap-1.5 rounded border px-2 py-1 transition-colors ${
                  config?.is_privacy_mode
                    ? 'border-rose-500/30 bg-rose-500/20 text-rose-400'
                    : 'border-white/10 bg-white/5 text-white/40'
                }`}
              >
                <ShieldCheck className="h-3 w-3" /> Privacy Mode
              </button>
              <button
                type="button"
                onClick={() => {
                  const newCompact = !config?.is_compact_mode;
                  void updateConfig({is_compact_mode: newCompact});
                  void executeCommand(`Compact Mode ${newCompact ? 'Enabled' : 'Disabled'}`);
                }}
                className={`flex items-center gap-1.5 rounded border px-2 py-1 transition-colors ${
                  config?.is_compact_mode
                    ? 'border-[color-mix(in_srgb,var(--ft-accent)_35%,var(--ft-border))] bg-[color-mix(in_srgb,var(--ft-accent)_18%,transparent)] text-[var(--ft-accent)]'
                    : 'border-white/10 bg-white/5 text-white/40'
                }`}
              >
                <Filter className="h-3 w-3" /> Compact Mode
              </button>
            </div>

            <div className="custom-scrollbar mb-4 min-h-0 flex-1 space-y-2 overflow-y-auto">
              <div className="font-bold text-emerald-500/60">MEGAcmd Interactive Terminal v1.0.0</div>
              <div className="italic text-white/40">Type &apos;mega-help&apos; for available commands.</div>
              {displayedTerminal.map((entry, i) => (
                <div key={i} className="group/entry relative space-y-1">
                  <div className="flex gap-2 text-emerald-400">
                    <span
                      className="shrink-0 text-white/50"
                      title={(entry.source ?? 'preset') === 'manual' ? 'Typed in terminal' : 'Preset / quick action'}
                    >
                      {(entry.source ?? 'preset') === 'manual' ? (
                        <Keyboard className="h-3.5 w-3.5" aria-hidden />
                      ) : (
                        <Zap className="h-3.5 w-3.5 opacity-70" aria-hidden />
                      )}
                    </span>
                    <span className="font-bold">{entry.cmd}</span>
                  </div>
                  <div className="relative whitespace-pre-wrap pl-6 text-white/70">
                    {entry.out}
                    <button
                      type="button"
                      onClick={() => void copyToClipboard(entry.out)}
                      className="absolute right-0 top-0 rounded p-1 opacity-0 transition-opacity hover:bg-white/10 group-hover/entry:opacity-100"
                      title="Copy output"
                    >
                      <Copy className="h-3 w-3 text-white/40" />
                    </button>
                  </div>
                </div>
              ))}
              <div ref={terminalEndRef} />
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                void executeCommand();
              }}
              className="flex items-center gap-3 rounded-xl border border-white/10 bg-black/40 px-4 py-2 transition-all focus-within:ring-1 focus-within:ring-emerald-500/50"
            >
              <span className="font-bold text-emerald-500" aria-hidden>{'>'}</span>
              <input
                type="text"
                value={terminalInput}
                onChange={(e) => setTerminalInput(e.target.value)}
                placeholder="Enter MEGAcmd command..."
                className="flex-1 border-none bg-transparent text-white placeholder:text-white/20 focus:outline-none"
              />
              <button type="submit" className="rounded-lg p-1 text-emerald-500 transition-colors hover:bg-white/10">
                <Send className="h-4 w-4" />
              </button>
            </form>
          </div>
        ) : (
          <div className="custom-scrollbar max-h-[min(70vh,calc(100vh-14rem))] min-h-[280px] overflow-y-auto p-4 font-mono text-[11px] leading-relaxed text-[var(--muted-foreground)]">
            {filteredLogs.length === 0 ? (
              <div className="py-10 text-center italic opacity-40">No matching logs found</div>
            ) : (
              filteredLogs.map((log, i) => (
                <div key={i} className="group/log mb-1 flex gap-3">
                  <span className="shrink-0 text-white/20">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                  <span
                    className={`w-16 shrink-0 font-bold ${
                      log.level === 'ERROR'
                        ? 'text-rose-500'
                        : log.level === 'WARN'
                          ? 'text-amber-500'
                          : log.level === 'SUCCESS'
                            ? 'text-emerald-500'
                            : 'text-[var(--ft-accent)]'
                    }`}
                  >
                    {log.level}
                  </span>
                  <span className="w-20 shrink-0 text-[9px] font-bold uppercase tracking-wider text-white/40">
                    {log.category}
                  </span>
                  <span className={`flex-1 ${log.level === 'ERROR' ? 'text-rose-400' : 'text-white/70'}`}>
                    {log.message}
                    {log.tag && (
                      <span className="ml-2 rounded bg-white/5 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-tighter text-white/30 transition-colors group-hover/log:text-[var(--ft-accent)]">
                        #{log.tag}
                      </span>
                    )}
                  </span>
                </div>
              ))
            )}
            <div ref={logEndRef} />
          </div>
        )}
      </div>
    </div>
  );
}
