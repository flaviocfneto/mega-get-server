import {LogIn, LogOut, Moon, Settings, ShieldCheck, Sun, Timer, Activity} from 'lucide-react';
import type {AccountInfo, AppConfig} from '../types';
import {accountTypeLabel} from '../lib/accountLabels';
import {ftBtnPrimarySm, ftFocusRing} from '../lib/ftUi';

type Props = {
  config: AppConfig | null;
  accountInfo: AccountInfo | null;
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  onOpenSettings: () => void;
  onOpenLogin: () => void;
  onLogout: () => void;
};

export function AppHeader({
  config,
  accountInfo,
  theme,
  toggleTheme,
  onOpenSettings,
  onOpenLogin,
  onLogout,
}: Props) {
  return (
    <header className="sticky top-0 z-50 border-b border-[var(--ft-border)] bg-[var(--card)]/90 backdrop-blur-md">
      <div className="flex h-16 w-full items-center justify-between px-4">
        <div className="flex min-w-0 items-center gap-3">
          <img
            src="/icons/ft-icon-app.svg"
            alt=""
            className="h-10 w-10 shrink-0 rounded-xl border border-[var(--ft-border)] bg-[var(--card)] p-1.5"
          />
          <div className="min-w-0">
            <img
              src="/branding/ft-logo-wordmark.svg"
              alt="FileTugger"
              className="h-7 max-w-[min(220px,40vw)] object-contain"
            />
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-[var(--muted-foreground)]">
                One queue, many sources
              </p>
              {config?.is_scheduling_enabled && (
                <div className="flex animate-pulse items-center gap-1 rounded border border-[var(--ft-warning)]/30 bg-[var(--ft-warning-bg)] px-1.5 py-0.5 text-[9px] font-bold uppercase text-[var(--ft-warning)]">
                  <Timer className="h-2.5 w-2.5" aria-hidden />
                  Scheduled
                </div>
              )}
              {config?.watch_folder_enabled && (
                <div className="flex items-center gap-1 rounded border border-[var(--ft-success)]/30 bg-[var(--ft-success-bg)] px-1.5 py-0.5 text-[9px] font-bold uppercase text-[var(--ft-success)]">
                  <Activity className="h-2.5 w-2.5" aria-hidden />
                  Watch folder
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          {accountInfo?.is_logged_in ? (
            <div className="flex max-w-[min(100%,14rem)] items-center gap-2 rounded-2xl border border-[var(--ft-border)] bg-[var(--muted)]/50 px-2 py-1.5 sm:max-w-none sm:gap-3 sm:px-3">
              <div className="flex min-w-0 flex-1 flex-col items-end text-right">
                <span
                  className={`block truncate text-xs font-bold text-[var(--foreground)] ${
                    config?.is_privacy_mode ? 'blur-sm select-none' : ''
                  }`}
                >
                  {accountInfo.email}
                </span>
                <span className="mt-0.5 flex items-center justify-end gap-1 text-[9px] font-bold uppercase tracking-widest text-[var(--ft-accent)]">
                  <ShieldCheck className="h-2.5 w-2.5 shrink-0" aria-hidden />
                  {accountTypeLabel(accountInfo.account_type)} account
                </span>
              </div>
              <button
                type="button"
                onClick={onLogout}
                className={`shrink-0 rounded-lg p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--ft-danger-bg)] hover:text-[var(--ft-danger)] ${ftFocusRing}`}
                title="Log out"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <button type="button" onClick={onOpenLogin} className={`hidden sm:flex ${ftBtnPrimarySm} ${ftFocusRing} gap-2`}>
              <LogIn className="h-4 w-4" />
              Log in to MEGA
            </button>
          )}

          <button
            type="button"
            onClick={toggleTheme}
            className={`rounded-xl border border-[var(--ft-border)] bg-[var(--muted)] p-2 text-[var(--foreground)] transition-colors hover:bg-[var(--border)] ${ftFocusRing}`}
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          >
            {theme === 'light' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
          </button>

          <button
            type="button"
            onClick={onOpenSettings}
            className={`rounded-xl border border-[var(--ft-border)] bg-[var(--muted)] p-2 text-[var(--foreground)] transition-colors hover:bg-[var(--border)] ${ftFocusRing}`}
            title="Settings"
          >
            <Settings className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  );
}
