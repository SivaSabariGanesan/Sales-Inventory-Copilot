/**
 * Data Import API service client.
 */

export async function fetchImportStatus() {
  const response = await fetch('/api/import/status');
  if (!response.ok) {
    throw new Error(`Failed to fetch database status: ${response.status}`);
  }
  return await response.json();
}

export async function previewSingleCsv(file, datasetType) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('dataset_type', datasetType);

  const response = await fetch('/api/import/preview', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Validation request failed: ${response.status}`);
  }
  return await response.json();
}

export async function previewAllCsv(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/import/preview-all', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `All.csv validation failed: ${response.status}`);
  }
  return await response.json();
}

export async function importSingleDataset(file, datasetType) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`/api/import/${datasetType}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Import failed: ${response.status}`);
  }
  return await response.json();
}

export async function importAllCombined(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/import/all', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Combined import failed: ${response.status}`);
  }
  return await response.json();
}

export function getTemplateUrl(templateName) {
  return `/api/import/templates/${templateName}`;
}

export async function resetToDemoData() {
  const response = await fetch('/api/import/reset-demo', {
    method: 'POST',
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Reset failed: ${response.status}`);
  }
  return await response.json();
}
