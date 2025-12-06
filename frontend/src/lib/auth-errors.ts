import { AxiosError } from "axios";

export interface AuthError {
  message: string;
  code?: string;
  status?: number;
  type: "validation" | "authentication" | "network" | "server" | "unknown";
}

/**
 * Parse authentication error responses from the API
 */
export function parseAuthError(error: unknown): AuthError {
  if (error instanceof AxiosError) {
    const status = error.response?.status;
    const data = error.response?.data;

    // Extract error message from various response formats
    let message = "An unexpected error occurred";
    let type: AuthError["type"] = "unknown";

    if (typeof data === "string") {
      message = data;
    } else if (data?.detail) {
      // FastAPI validation errors or custom error detail
      if (typeof data.detail === "string") {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        // Pydantic validation errors
        message = data.detail.map((err: { msg: string }) => err.msg).join(", ");
      }
    } else if (data?.message) {
      message = data.message;
    }

    // Determine error type based on status code
    if (status === 401) {
      type = "authentication";
    } else if (status === 422) {
      type = "validation";
    } else if (error.code === "ERR_NETWORK" || !status) {
      type = "network";
    } else if (status && status >= 500) {
      type = "server";
    }

    return {
      message,
      status,
      code: data?.code || error.code,
      type,
    };
  }

  if (error instanceof Error) {
    return {
      message: error.message,
      type: "unknown",
    };
  }

  return {
    message: "An unexpected error occurred",
    type: "unknown",
  };
}

/**
 * Map authentication error codes to user-friendly messages
 * Requirements: 5.1, 5.2, 5.3
 */
export function getAuthErrorMessage(error: AuthError): string {
  // Handle specific error types
  switch (error.type) {
    case "authentication":
      // Invalid credentials (401)
      if (
        error.message.toLowerCase().includes("invalid") ||
        error.message.toLowerCase().includes("incorrect")
      ) {
        return "Invalid email or password";
      }
      if (error.message.toLowerCase().includes("inactive")) {
        return "Account is inactive";
      }
      if (error.message.toLowerCase().includes("expired")) {
        return "Your session has expired. Please log in again.";
      }
      return "Invalid email or password";

    case "validation":
      // Validation errors (422)
      if (error.message.toLowerCase().includes("email")) {
        return "Please enter a valid email address";
      }
      if (error.message.toLowerCase().includes("password")) {
        return "Please enter a valid password";
      }
      return "Please check your email and password";

    case "network":
      // Network errors
      return "Unable to connect. Please check your internet connection.";

    case "server":
      // Server errors (500+)
      return "Something went wrong. Please try again later.";

    default:
      // Unknown errors
      return error.message || "An unexpected error occurred. Please try again.";
  }
}

/**
 * Handle authentication error and return user-friendly message
 * This is the main function to use when handling auth errors
 */
export function handleAuthError(error: unknown): string {
  const authError = parseAuthError(error);
  return getAuthErrorMessage(authError);
}

/**
 * Check if an error is an authentication error (401)
 */
export function isAuthenticationError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return error.response?.status === 401;
  }
  return false;
}

/**
 * Check if an error is a network error
 */
export function isNetworkError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return error.code === "ERR_NETWORK" || !error.response;
  }
  return false;
}

/**
 * Check if an error is a validation error (422)
 */
export function isValidationError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return error.response?.status === 422;
  }
  return false;
}
