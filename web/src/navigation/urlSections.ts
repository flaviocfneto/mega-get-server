/**
 * Hash-based section URLs (no server change): #/transfers | #/history | #/analytics | #/system | #/system/terminal
 */
import type {AppSectionId} from './primaryNav';

const SECTIONS: readonly AppSectionId[] = ['transfers', 'history', 'analytics', 'system'] as const;

function isSectionId(s: string): s is AppSectionId {
  return (SECTIONS as readonly string[]).includes(s);
}

export type ParsedAppHash = {
  section: AppSectionId;
  /** Only meaningful when section === 'system'. */
  systemTab: 'log' | 'terminal';
};

export function parseAppHash(hash: string): ParsedAppHash {
  const raw = hash.replace(/^#/, '').trim();
  const path = raw.startsWith('/') ? raw.slice(1) : raw;
  const parts = path.split('/').filter(Boolean);
  const head = parts[0] || 'transfers';

  if (!isSectionId(head)) {
    return {section: 'transfers', systemTab: 'log'};
  }
  if (head !== 'system') {
    return {section: head, systemTab: 'log'};
  }
  const systemTab = parts[1] === 'terminal' ? 'terminal' : 'log';
  return {section: 'system', systemTab};
}

export function buildAppHash(section: AppSectionId, systemTab: 'log' | 'terminal'): string {
  if (section === 'system' && systemTab === 'terminal') {
    return '#/system/terminal';
  }
  if (section === 'system') {
    return '#/system';
  }
  return `#/${section}`;
}
