import type {
  AuthTokens,
  Follow,
  Notification,
  Paginated,
  Post,
  User,
} from "../types";

export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8050";
export const WS_BASE_URL: string =
  (import.meta.env.VITE_WS_BASE_URL as string | undefined) ?? "ws://localhost:8050";

const ACCESS_TOKEN_KEY = "socialpulse_access_token";
const REFRESH_TOKEN_KEY = "socialpulse_refresh_token";

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(tokens: AuthTokens): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((options.headers as Record<string, string>) || {}),
  };

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (response.status === 401 && retry && getRefreshToken()) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      return request<T>(path, options, false);
    }
    clearTokens();
  }

  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(body || response.statusText, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

async function tryRefreshToken(): Promise<boolean> {
  const refresh = getRefreshToken();
  if (!refresh) return false;
  const response = await fetch(`${API_BASE_URL}/api/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!response.ok) return false;
  const data = (await response.json()) as { access: string };
  localStorage.setItem(ACCESS_TOKEN_KEY, data.access);
  return true;
}

export const api = {
  register: (payload: { username: string; email: string; password: string }) =>
    request<User>("/api/auth/register/", { method: "POST", body: JSON.stringify(payload) }),

  login: async (username: string, password: string): Promise<AuthTokens> => {
    const tokens = await request<AuthTokens>("/api/auth/token/", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    setTokens(tokens);
    return tokens;
  },

  me: () => request<User>("/api/auth/me/"),

  feed: () => request<Post[]>("/api/posts/feed/"),

  listPosts: () => request<Paginated<Post>>("/api/posts/"),

  createPost: (content: string) =>
    request<Post>("/api/posts/", { method: "POST", body: JSON.stringify({ content }) }),

  likePost: (postId: number) =>
    request<{ liked: boolean; likes_count: number }>(`/api/posts/${postId}/like/`, { method: "POST" }),

  unlikePost: (postId: number) =>
    request<{ unliked: boolean; likes_count: number }>(`/api/posts/${postId}/unlike/`, { method: "POST" }),

  createComment: (postId: number, content: string) =>
    request(`/api/comments/`, { method: "POST", body: JSON.stringify({ post: postId, content }) }),

  follow: (userId: number) =>
    request<Follow>("/api/follows/", { method: "POST", body: JSON.stringify({ following: userId }) }),

  unfollow: (followId: number) => request<void>(`/api/follows/${followId}/`, { method: "DELETE" }),

  listNotifications: () => request<Paginated<Notification>>("/api/notifications/"),

  markNotificationRead: (id: number) =>
    request<Notification>(`/api/notifications/${id}/mark_read/`, { method: "POST" }),
};

export { ApiError };
