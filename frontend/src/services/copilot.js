/**
 * Copilot API service client for Natural-Language questions.
 */

export async function queryCopilot(question) {
  const cleanQuestion = (question || '').trim();
  if (!cleanQuestion) {
    throw new Error('Please enter a question to ask Copilot.');
  }

  const response = await fetch('/api/copilot/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question: cleanQuestion }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Copilot query failed: ${response.status} ${response.statusText}`
    );
  }

  return await response.json();
}
