import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  startImport,
  getImportStatus,
  getImportHistory,
  checkExistingData,
} from "@/lib/api/import";
import {
  ImportStartRequest,
  ImportStartResponse,
  ImportStatusResponse,
  ImportHistoryResponse,
  ExistingDataCheckRequest,
  ExistingDataCheckResponse,
} from "@/types/import";

/**
 * Hook to start a new import job
 *
 * @returns Mutation hook for starting imports
 */
export function useStartImport() {
  const queryClient = useQueryClient();

  return useMutation<ImportStartResponse, Error, ImportStartRequest>({
    mutationFn: startImport,
    onSuccess: () => {
      // Invalidate import history to show the new job
      queryClient.invalidateQueries({
        queryKey: ["import", "history"],
      });
    },
    onError: (error: unknown) => {
      // Log error for debugging
      console.error("Import start error:", error);

      // The error will be handled by the component using this hook
      // We just ensure it's properly formatted
    },
  });
}

/**
 * Hook to get the status of an import job with optional polling
 *
 * @param jobId - The import job ID
 * @param options - Query options including polling configuration
 * @returns Query hook for import status
 */
export function useImportStatus(
  jobId: string | null,
  options?: {
    enabled?: boolean;
    refetchInterval?: number | false;
  }
) {
  const queryClient = useQueryClient();

  return useQuery<ImportStatusResponse, Error>({
    queryKey: ["import", "status", jobId],
    queryFn: () => getImportStatus(jobId!),
    enabled: !!jobId && (options?.enabled ?? true),
    refetchInterval: (query) => {
      const data = query.state.data;
      // Stop polling if job is completed or failed
      if (data?.status === "completed" || data?.status === "failed") {
        // Invalidate import history when job completes
        queryClient.invalidateQueries({
          queryKey: ["import", "history"],
        });
        return false;
      }
      // Default to 2 seconds polling interval for running jobs
      return options?.refetchInterval ?? 2000;
    },
    // Keep previous data while refetching to avoid UI flicker
    placeholderData: (previousData) => previousData,
  });
}

/**
 * Hook to get import history with optional filters
 *
 * @param params - Query parameters for filtering history
 * @returns Query hook for import history
 */
export function useImportHistory(params?: {
  limit?: number;
  offset?: number;
  season?: number;
  status?: string;
}) {
  return useQuery<ImportHistoryResponse, Error>({
    queryKey: ["import", "history", params],
    queryFn: () => getImportHistory(params),
    // Refetch every 10 seconds to show running imports
    refetchInterval: 10000,
  });
}

/**
 * Hook to check for existing data before import
 *
 * @returns Mutation hook for checking existing data
 */
export function useCheckExistingData() {
  return useMutation<
    ExistingDataCheckResponse,
    Error,
    ExistingDataCheckRequest
  >({
    mutationFn: checkExistingData,
  });
}
