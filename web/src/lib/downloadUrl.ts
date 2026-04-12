/** True if the string is an http(s) URL with a host (MEGA or generic direct download). */
export function isHttpOrHttpsUrl(raw: string): boolean {
  try {
    const u = new URL(raw.trim());
    if (u.protocol !== 'http:' && u.protocol !== 'https:') return false;
    return Boolean(u.hostname);
  } catch {
    return false;
  }
}
