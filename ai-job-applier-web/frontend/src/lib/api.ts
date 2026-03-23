const trimSlash = (value: string) => value.replace(/\/+$/, "");

const envHttpBase = (import.meta.env.VITE_API_BASE_URL || "").trim();
const envWsBase = (import.meta.env.VITE_WS_BASE_URL || "").trim();
const defaultOrigin = typeof window !== "undefined" ? window.location.origin : "";
const computedApiBase = envHttpBase || defaultOrigin;
const computedWsBase =
  envWsBase || (computedApiBase ? computedApiBase.replace(/^http/i, "ws") : "");

export const API_BASE_URL = trimSlash(computedApiBase);
export const WS_BASE_URL = trimSlash(computedWsBase);

export const apiUrl = (path: string) => {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalized}`;
};

export const wsUrl = (path: string) => {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${WS_BASE_URL}${normalized}`;
};

export const getAuthToken = () => {
  if (typeof window === "undefined") {
    return "";
  }
  return window.localStorage.getItem("token") || "";
};

export const authHeaders = (headers: Record<string, string> = {}) => {
  const token = getAuthToken();
  return token ? { ...headers, Authorization: `Bearer ${token}` } : headers;
};
