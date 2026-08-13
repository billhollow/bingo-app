export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : `Request failed with status ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

interface RequestOptions {
  token?: string;
}

async function request<T>(
  method: string,
  path: string,
  body: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await response.json() : undefined;

  if (!response.ok) {
    throw new ApiError(response.status, data ?? response.statusText);
  }
  return data as T;
}

export const apiGet = <T>(path: string, options?: RequestOptions) =>
  request<T>("GET", path, undefined, options);

export const apiPost = <T>(path: string, body?: unknown, options?: RequestOptions) =>
  request<T>("POST", path, body, options);

/** Best-effort extraction of a human-readable message from an ApiError. */
export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (typeof err.detail === "string") return err.detail;
    if (err.detail && typeof err.detail === "object") {
      const detail = err.detail as Record<string, unknown>;
      if (typeof detail.detail === "string") return detail.detail;
      const [firstKey] = Object.keys(detail);
      if (firstKey) {
        const value = detail[firstKey];
        const message = Array.isArray(value) ? value[0] : value;
        return `${firstKey}: ${String(message)}`;
      }
    }
    return err.message;
  }
  return err instanceof Error ? err.message : String(err);
}
