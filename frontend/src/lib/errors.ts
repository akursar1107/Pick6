import { AxiosError } from "axios";

export interface ApiError {
  message: string;
  code?: string;
  status?: number;
}

/**
 * Parse API error response and extract error information
 */
export function parseApiError(error: unknown): ApiError {
  if (error instanceof AxiosError) {
    const status = error.response?.status;
    const data = error.response?.data;

    // Extract error message from various response formats
    let message = "An unexpected error occurred";

    if (typeof data === "string") {
      message = data;
    } else if (data?.detail) {
      // FastAPI validation errors or custom error detail
      if (typeof data.detail === "string") {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        // Pydantic validation errors
        message = data.detail.map((err: any) => err.msg).join(", ");
      }
    } else if (data?.message) {
      message = data.message;
    }

    return {
      message,
      status,
      code: data?.code,
    };
  }

  if (error instanceof Error) {
    return {
      message: error.message,
    };
  }

  return {
    message: "An unexpected error occurred",
  };
}

/**
 * Map error codes and status to user-friendly messages
 */
export function getUserFriendlyErrorMessage(error: ApiError): string {
  // Handle specific status codes
  switch (error.status) {
    case 400:
      // Check for specific validation messages
      if (error.message.toLowerCase().includes("kickoff")) {
        return "Cannot modify pick after game kickoff";
      }
      if (error.message.toLowerCase().includes("duplicate")) {
        return "You already have a pick for this game";
      }
      return error.message || "Invalid request. Please check your input.";

    case 401:
      return "You must be logged in to perform this action";

    case 403:
      return "You are not authorized to perform this action";

    case 404:
      if (error.message.toLowerCase().includes("game")) {
        return "Game not found";
      }
      if (error.message.toLowerCase().includes("player")) {
        return "Player not found";
      }
      if (error.message.toLowerCase().includes("pick")) {
        return "Pick not found";
      }
      return "The requested resource was not found";

    case 409:
      return "This action conflicts with existing data";

    case 422:
      return "Invalid data provided. Please check your input.";

    case 500:
      return "Server error. Please try again later.";

    case 503:
      return "Service temporarily unavailable. Please try again later.";

    default:
      return error.message || "An unexpected error occurred";
  }
}

/**
 * Handle API error and return user-friendly message
 */
export function handleApiError(error: unknown): string {
  const apiError = parseApiError(error);
  return getUserFriendlyErrorMessage(apiError);
}
