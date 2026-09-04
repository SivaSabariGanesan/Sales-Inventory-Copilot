/**
 * Settings and Gemini Configuration API service client.
 */

export async function fetchGeminiSettings() {
  const response = await fetch('/api/settings/gemini');
  if (!response.ok) {
    throw new Error(`Failed to fetch Gemini settings: ${response.status} ${response.statusText}`);
  }
  return await response.json();
}

export async function saveGeminiSettings({ apiKey, model }) {
  const response = await fetch('/api/settings/gemini', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      api_key: apiKey,
      model: model || undefined,
    }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to save Gemini key: ${response.status}`);
  }
  return await response.json();
}

export async function testGeminiConnection() {
  const response = await fetch('/api/settings/gemini/test', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Connection test failed: ${response.status}`);
  }
  return await response.json();
}
