/**
 * Financial and Value Analytics API Client.
 */

export async function fetchValueAnalytics(params = {}) {
  const query = new URLSearchParams();
  if (params.storeId) query.append('store_id', params.storeId);
  if (params.category) query.append('category', params.category);
  if (params.productId) query.append('product_id', params.productId);
  if (params.startDate) query.append('start_date', params.startDate);
  if (params.endDate) query.append('end_date', params.endDate);

  const qs = query.toString();
  const url = `/api/analytics/value${qs ? `?${qs}` : ''}`;

  const response = await fetch(url);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch value analytics: ${response.status}`);
  }
  return await response.json();
}
