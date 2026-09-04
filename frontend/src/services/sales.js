/**
 * Sales API service client for Sales Anomaly Signals (Spikes & Drops).
 */

export async function fetchSalesAnomalies({
  storeId = null,
  category = null,
  status = null,
  recentDays = 7,
  baselineDays = 30,
} = {}) {
  const params = new URLSearchParams();
  if (storeId && storeId !== 'ALL') params.append('store_id', storeId);
  if (category && category !== 'ALL') params.append('category', category);
  if (status && status !== 'ALL') params.append('status', status);
  if (recentDays) params.append('recent_days', recentDays);
  if (baselineDays) params.append('baseline_days', baselineDays);

  const url = `/api/sales/anomalies${params.toString() ? `?${params.toString()}` : ''}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch sales anomalies: ${response.status} ${response.statusText}`);
  }
  return await response.json();
}
