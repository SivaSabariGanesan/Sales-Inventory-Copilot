/**
 * Stores API service client.
 */

export async function fetchStores({ search = '' } = {}) {
  const params = new URLSearchParams();
  if (search && search.trim()) params.append('search', search.trim());

  const url = `/api/stores${params.toString() ? `?${params.toString()}` : ''}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch store network: ${response.status} ${response.statusText}`);
  }
  return await response.json();
}
