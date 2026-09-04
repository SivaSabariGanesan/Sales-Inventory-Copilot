/**
 * Recommendations API service client.
 */

export async function fetchRecommendations({
  storeId = null,
  category = null,
  priority = null,
  action = null,
} = {}) {
  const params = new URLSearchParams();
  if (storeId && storeId !== 'ALL') params.append('store_id', storeId);
  if (category && category !== 'ALL') params.append('category', category);
  if (priority && priority !== 'ALL') params.append('priority', priority);
  if (action && action !== 'ALL') params.append('action', action);

  const url = `/api/recommendations${params.toString() ? `?${params.toString()}` : ''}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch recommendations: ${response.status} ${response.statusText}`);
  }
  return await response.json();
}

export async function fetchTodaysAttention(limit = 6) {
  const response = await fetch(`/api/recommendations/today?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch today's attention items: ${response.status} ${response.statusText}`);
  }
  return await response.json();
}
