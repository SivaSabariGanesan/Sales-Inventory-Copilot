/**
 * Authentication service client communicating with the FastAPI backend.
 */

export async function fetchAuthStatus() {
  try {
    const response = await fetch('/api/auth/status');
    if (!response.ok) {
      throw new Error(`Auth status request failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    return {
      authenticated: false,
      user: null,
      oauth_configured: false,
      message: error.message || 'Unable to connect to authentication service.',
    };
  }
}
