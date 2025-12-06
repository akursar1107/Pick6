import axios from "axios";
import { toast } from "sonner";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized errors
      const currentPath = window.location.pathname;
      const isLoginPage = currentPath === "/login";

      // Clear token from localStorage
      localStorage.removeItem("access_token");

      // Clear auth store state
      // We import dynamically to avoid circular dependency issues
      const { useAuthStore } = await import("../stores/authStore");

      // Clear store state without calling logout API (to avoid infinite loop)
      useAuthStore.setState({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      });

      // Show error toast for session expiration (but not on login page)
      if (!isLoginPage) {
        toast.error("Your session has expired. Please log in again.");
      }

      // Redirect to login page
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
