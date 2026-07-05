import axios from "axios";

export const API_BASE_URL =
  (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000/api/v1";

// Uploaded files (e.g. avatars) are served from the API origin root, not under /api/v1.
export const API_ORIGIN = API_BASE_URL.replace(/\/api\/v1\/?$/, "");

export function resolveUploadUrl(path: string | null | undefined): string | undefined {
  if (!path) return undefined;
  return `${API_ORIGIN}${path}`;
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

let isRefreshing = false;
let pendingQueue: Array<() => void> = [];

function flushQueue() {
  pendingQueue.forEach((resolve) => resolve());
  pendingQueue = [];
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const status = error.response?.status;
    const isAuthEndpoint = originalRequest?.url?.includes("/auth/");

    if (status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;

      if (isRefreshing) {
        await new Promise<void>((resolve) => pendingQueue.push(resolve));
        return apiClient(originalRequest);
      }

      isRefreshing = true;
      try {
        await apiClient.post("/auth/refresh");
        flushQueue();
        return apiClient(originalRequest);
      } catch (refreshError) {
        flushQueue();
        window.dispatchEvent(new CustomEvent("ams:session-expired"));
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

export interface ApiErrorBody {
  success: false;
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

export function getApiErrorMessage(err: unknown, fallback = "Something went wrong"): string {
  if (axios.isAxiosError(err)) {
    const body = err.response?.data as ApiErrorBody | undefined;
    if (body?.error?.message) return body.error.message;
  }
  return fallback;
}
