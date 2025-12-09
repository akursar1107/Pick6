/**
 * Utility functions for handling import-related errors
 */

export interface ImportError {
  message: string;
  detail?: string;
  canRetry: boolean;
}

/**
 * Parse and format import error messages for user display
 */
export function parseImportError(error: any): ImportError {
  // Handle axios error response
  if (error?.response?.data?.detail) {
    const detail = error.response.data.detail;

    // Check for specific error types
    if (detail.includes("already in progress")) {
      return {
        message: "Import Already Running",
        detail:
          "An import is already in progress for this season. Please wait for it to complete before starting a new import.",
        canRetry: false,
      };
    }

    if (detail.includes("Week numbers must be between")) {
      return {
        message: "Invalid Week Selection",
        detail: detail,
        canRetry: true,
      };
    }

    if (detail.includes("Season must be between")) {
      return {
        message: "Invalid Season",
        detail: detail,
        canRetry: true,
      };
    }

    if (detail.includes("network") || detail.includes("Network")) {
      return {
        message: "Network Error",
        detail:
          "Failed to connect to the NFL data service. Please check your internet connection and try again.",
        canRetry: true,
      };
    }

    if (detail.includes("timeout") || detail.includes("Timeout")) {
      return {
        message: "Request Timeout",
        detail:
          "The import request timed out. This may be due to a slow connection or server issues. Please try again.",
        canRetry: true,
      };
    }

    if (detail.includes("not found") || detail.includes("Not found")) {
      return {
        message: "Import Job Not Found",
        detail:
          "The import job could not be found. It may have expired or been deleted.",
        canRetry: false,
      };
    }

    if (detail.includes("permission") || detail.includes("Permission")) {
      return {
        message: "Permission Denied",
        detail:
          "You do not have permission to perform this import. Please contact an administrator.",
        canRetry: false,
      };
    }

    // Generic error with detail
    return {
      message: "Import Error",
      detail: detail,
      canRetry: true,
    };
  }

  // Handle network errors
  if (
    error?.code === "ERR_NETWORK" ||
    error?.message?.includes("Network Error")
  ) {
    return {
      message: "Network Error",
      detail:
        "Unable to connect to the server. Please check your internet connection and try again.",
      canRetry: true,
    };
  }

  // Handle timeout errors
  if (error?.code === "ECONNABORTED" || error?.message?.includes("timeout")) {
    return {
      message: "Request Timeout",
      detail: "The request took too long to complete. Please try again.",
      canRetry: true,
    };
  }

  // Generic error
  return {
    message: "Unexpected Error",
    detail:
      error?.message || "An unexpected error occurred. Please try again later.",
    canRetry: true,
  };
}

/**
 * Get user-friendly error message for display in toast notifications
 */
export function getImportErrorToastMessage(error: any): string {
  const parsedError = parseImportError(error);
  return parsedError.detail || parsedError.message;
}

/**
 * Get error message for display in error UI components
 */
export function getImportErrorDisplayMessage(error: any): {
  title: string;
  message: string;
  canRetry: boolean;
} {
  const parsedError = parseImportError(error);
  return {
    title: parsedError.message,
    message: parsedError.detail || parsedError.message,
    canRetry: parsedError.canRetry,
  };
}
