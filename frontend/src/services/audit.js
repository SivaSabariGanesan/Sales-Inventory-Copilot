/**
 * Audit and Gemini Usage Tracking service client.
 */

export async function fetchAuditLogs(params = {}) {
  const query = new URLSearchParams();
  if (params.page) query.append('page', params.page);
  if (params.pageSize) query.append('page_size', params.pageSize);
  if (params.search) query.append('search', params.search);
  if (params.intent) query.append('intent', params.intent);
  if (params.status) query.append('status', params.status);
  if (params.cacheHit !== undefined && params.cacheHit !== '') query.append('cache_hit', params.cacheHit);
  if (params.needsHumanReview !== undefined && params.needsHumanReview !== '') query.append('needs_human_review', params.needsHumanReview);

  const qs = query.toString();
  const url = `/api/audit${qs ? `?${qs}` : ''}`;

  const response = await fetch(url);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch audit logs: ${response.status}`);
  }
  return await response.json();
}

export async function fetchAuditLogDetail(logId) {
  const response = await fetch(`/api/audit/${logId}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch audit log detail: ${response.status}`);
  }
  return await response.json();
}

export async function fetchGeminiUsage() {
  const response = await fetch('/api/usage');
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch usage metrics: ${response.status}`);
  }
  return await response.json();
}
