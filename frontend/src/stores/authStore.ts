import { create } from "zustand";
import { toast } from "sonner";
import { User } from "../types/auth";
import * as authApi from "../lib/api/auth";

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loadUserFromToken: () => Promise<void>;
  setUser: (user: User) => void;
}

const TOKEN_KEY = "access_token";

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem(TOKEN_KEY),
  isAuthenticated: false,
  isLoading: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true });
    try {
      const response = await authApi.login(email, password);

      // Store token in localStorage
      localStorage.setItem(TOKEN_KEY, response.access_token);

      // Update store state
      set({
        user: response.user,
        token: response.access_token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: () => {
    // Call logout API (fire and forget)
    authApi.logout().catch((error) => {
      console.warn("Logout API call failed:", error);
    });

    // Clear token from localStorage
    localStorage.removeItem(TOKEN_KEY);

    // Clear store state
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });

    // Show info toast
    toast.info("You have been logged out");

    // Redirect to login page
    window.location.href = "/login";
  },

  loadUserFromToken: async () => {
    const token = localStorage.getItem(TOKEN_KEY);

    if (!token) {
      set({ isLoading: false, isAuthenticated: false });
      return;
    }

    set({ isLoading: true });

    try {
      // Validate token by fetching current user
      const user = await authApi.getCurrentUser();

      set({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      // Token is invalid or expired
      console.warn("Token validation failed:", error);
      localStorage.removeItem(TOKEN_KEY);
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },

  setUser: (user: User) => {
    set({ user });
  },
}));
