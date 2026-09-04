/**
 * Products API service client.
 */

export async function fetchProducts({ search = '', category = '', limit = null, offset = 0 } = {}) {
  const params = new URLSearchParams();
  if (search && search.trim()) params.append('search', search.trim());
  if (category && category !== 'ALL') params.append('category', category);
  if (limit) params.append('limit', limit);
  if (offset) params.append('offset', offset);

  const url = `/api/products${params.toString() ? `?${params.toString()}` : ''}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch product catalog: ${response.status} ${response.statusText}`);
  }
  return await response.json();
}
