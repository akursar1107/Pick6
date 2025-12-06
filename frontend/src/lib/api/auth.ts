import { apiClient } from "../api";
import { LoginRequest, LoginResponse, User } from "../../types/auth";

/**
 * Authenticate user with email and password
 * @param email - User's email address
 * @param password - User's password
 * @returns LoginResponse containing access token and user info
 */
export async function login(
  email: string,
  password: string
): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>("/auth/login", {
    email,
    password,
  } as LoginRequest);
  return response.data;
}

/**
 * Logout the current user
 * Note: This is primarily a client-side operation that clears the token
 * The backend endpoint is optional for this implementation
 */
export async function logout(): Promise<void> {
  try {
    // Optional: Call backend logout endpoint if it exists
    await apiClient.post("/auth/logout");
  } catch (error) {
    // Ignore errors - logout should always succeed on client side
    console.warn("Logout endpoint not available or failed:", error);
  }
}

/**
 * Get current authenticated user information
 * @returns User object for the currently authenticated user
 */
export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>("/auth/me");
  return response.data;
}
