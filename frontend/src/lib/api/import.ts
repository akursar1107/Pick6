import { apiClient } from "@/lib/api";
import {
  ImportStartRequest,
  ImportStartResponse,
  ImportStatusResponse,
  ImportHistoryResponse,
  ExistingDataCheckRequest,
  ExistingDataCheckResponse,
} from "@/types/import";

/**
 * Start a new NFL data import job
 */
export async function startImport(
  data: ImportStartRequest
): Promise<ImportStartResponse> {
  const response = await apiClient.post<ImportStartResponse>(
    "/admin/import/start",
    data
  );
  return response.data;
}

/**
 * Get the status of an import job
 */
export async function getImportStatus(
  jobId: string
): Promise<ImportStatusResponse> {
  const response = await apiClient.get<ImportStatusResponse>(
    `/admin/import/status/${jobId}`
  );
  return response.data;
}

/**
 * Get import history with optional filters
 */
export async function getImportHistory(params?: {
  limit?: number;
  offset?: number;
  season?: number;
  status?: string;
}): Promise<ImportHistoryResponse> {
  const response = await apiClient.get<ImportHistoryResponse>(
    "/admin/import/history",
    { params }
  );
  return response.data;
}

/**
 * Check for existing data before import
 */
export async function checkExistingData(
  data: ExistingDataCheckRequest
): Promise<ExistingDataCheckResponse> {
  const response = await apiClient.post<ExistingDataCheckResponse>(
    "/admin/import/check-existing",
    data
  );
  return response.data;
}
