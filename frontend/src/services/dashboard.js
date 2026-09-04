/**
 * Dashboard API service client for executive summary and store breakdown.
 */

export async function fetchDashboardSummary({
  storeId = null,
  category = null,
} = {}) {
  const params = new URLSearchParams();
  if (storeId && storeId !== 'ALL') params.append('store_id', storeId);
  if (category && category !== 'ALL') params.append('category', category);

  const url = `/api/dashboard/summary${params.toString() ? `?${params.toString()}` : ''}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard summary: ${response.status} ${response.statusText}`);
  }
  return await response.json();
}
