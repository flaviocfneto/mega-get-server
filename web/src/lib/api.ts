export class ApiError extends Error {
  status: number;
  details?: string;

  constructor(message: string, status: number, details?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

export type ApiFailure = {
  ok: false;
  status: number;
  message: string;
  details?: string;
};

export type ApiSuccess<T> = {
  ok: true;
  status: number;
  data: T;
};

export type ApiResult<T> = ApiSuccess<T> | ApiFailure;

export function isApiFailure<T>(result: ApiResult<T>): result is ApiFailure {
  return result.ok === false;
}

export function isApiSuccess<T>(result: ApiResult<T>): result is ApiSuccess<T> {
  return result.ok === true;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function extractErrorMessage(payload: unknown, status: number): { message: string; details?: string } {
  if (isRecord(payload)) {
    const detail = typeof payload.detail === 'string' ? payload.detail : undefined;
    const message = typeof payload.message === 'string' ? payload.message : detail;
    return {
      message: message ?? `Server returned ${status}`,
      details: detail,
    };
  }
  return { message: `Server returned ${status}` };
}

async function readJsonBody(res: Response): Promise<unknown> {
  const contentType = res.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new ApiError('Not a JSON response', res.status);
  }
  return (await res.json()) as unknown;
}

/**
 * JSON GET. Returns `unknown`; callers must narrow via `apiNormalize.ts` (or an explicit guard)
 * before using as a concrete shape — do not cast blindly.
 */
export async function apiGet(url: string): Promise<unknown> {
  const res = await fetch(url);
  if (!res.ok) {
    let parsed: unknown = null;
    try {
      parsed = await readJsonBody(res);
    } catch {
      parsed = null;
    }
    const err = extractErrorMessage(parsed, res.status);
    throw new ApiError(err.message, res.status, err.details);
  }
  return readJsonBody(res);
}

/**
 * JSON POST. Returns `unknown`; narrow with normalizers before use (same contract as `apiGet`).
 */
export async function apiPost(url: string, body?: unknown): Promise<unknown> {
  const res = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) {
    let parsed: unknown = null;
    try {
      parsed = await readJsonBody(res);
    } catch {
      parsed = null;
    }
    const err = extractErrorMessage(parsed, res.status);
    throw new ApiError(err.message, res.status, err.details);
  }
  return readJsonBody(res);
}

/**
 * POST with JSON body; success payloads are `unknown`. On success, pass `result.data` through
 * the appropriate normalizer from `apiNormalize.ts` before trusting fields.
 */
export async function apiPostResult(url: string, body?: unknown): Promise<ApiResult<unknown>> {
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body ?? {}),
    });
    if (!res.ok) {
      let parsed: unknown = null;
      try {
        parsed = await readJsonBody(res);
      } catch {
        parsed = null;
      }
      const err = extractErrorMessage(parsed, res.status);
      return { ok: false, status: res.status, message: err.message, details: err.details };
    }
    const data = await readJsonBody(res);
    return { ok: true, status: res.status, data };
  } catch {
    return { ok: false, status: 0, message: 'Network request failed before backend confirmation.' };
  }
}

/** DELETE; success body is `unknown` — normalize before use (same as `apiPostResult`). */
export async function apiDeleteResult(url: string): Promise<ApiResult<unknown>> {
  try {
    const res = await fetch(url, { method: 'DELETE' });
    if (!res.ok) {
      let parsed: unknown = null;
      try {
        parsed = await readJsonBody(res);
      } catch {
        parsed = null;
      }
      const err = extractErrorMessage(parsed, res.status);
      return { ok: false, status: res.status, message: err.message, details: err.details };
    }
    const data = await readJsonBody(res);
    return { ok: true, status: res.status, data };
  } catch {
    return { ok: false, status: 0, message: 'Network request failed before backend confirmation.' };
  }
}
