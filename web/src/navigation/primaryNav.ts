/**
 * Primary app sections — single source for sidebar (lg+) and bottom nav (<lg).
 * Breakpoint: lg (1024px); see AppShell layout in App.tsx.
 */
import {Activity, BarChart3, History, ScrollText} from 'lucide-react';
import type {LucideIcon} from 'lucide-react';

export type AppSectionId = 'transfers' | 'history' | 'analytics' | 'system';

export type PrimaryNavItem = {
  id: AppSectionId;
  label: string;
  /** Shorter label for bottom nav when space is tight. */
  shortLabel?: string;
  icon: LucideIcon;
};

export const PRIMARY_NAV: readonly PrimaryNavItem[] = [
  {id: 'transfers', label: 'Transfers', icon: Activity},
  {id: 'history', label: 'History and Queue', icon: History},
  {id: 'analytics', label: 'Analytics', icon: BarChart3},
  {id: 'system', label: 'Logs & Terminal', shortLabel: 'System', icon: ScrollText},
] as const;
