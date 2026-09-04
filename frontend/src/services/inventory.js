/**
 * Inventory API service client.
 */

export async function fetchStockoutRisks({
  storeId = null,
  category = null,
  riskLevel = null,
  lookbackDays = 14,
} = {}) {
  const params = new URLSearchParams();
  if (storeId) params.append('store_id', storeId);
  if (category && category !== 'ALL') params.append('category', category);
  if (riskLevel && riskLevel !== 'ALL') params.append('risk_level', riskLevel);
  if (lookbackDays) params.append('lookback_days', lookbackDays);

  const url = `/api/inventory/stockout-risks${params.toString() ? `?${params.toString()}` : ''}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch stock-out risks: ${response.status} ${response.statusText}`);
  }
  return await response.json();
}

export async function fetchInventoryMetadata() {
  const response = await fetch('/api/inventory/metadata');
  if (!response.ok) {
    throw new Error(`Failed to fetch inventory metadata: ${response.status} ${response.statusText}`);
  }
  return await response.json();
}
