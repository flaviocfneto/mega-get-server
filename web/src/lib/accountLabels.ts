import type {AccountInfo} from '../types';

export function accountTypeLabel(accountType: AccountInfo['account_type']): string {
  if (accountType === 'UNKNOWN') return 'MEGA';
  return accountType;
}
