export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const API_ENDPOINTS = {
  health: `${API_BASE_URL}/api/health`,
  status: `${API_BASE_URL}/api/status`,
  research: `${API_BASE_URL}/api/research`,
} as const;

// Primary health check endpoint (change to 'status' if your backend uses that)
export const HEALTH_CHECK_ENDPOINT = API_ENDPOINTS.health;
