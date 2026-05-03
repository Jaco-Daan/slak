// Thin wrapper over the backend (proxied via Vite at /api).

const BASE = '/api';

async function postFile(path, file) {
  const fd = new FormData();
  fd.append('file', file);
  const res = await fetch(`${BASE}${path}`, { method: 'POST', body: fd });
  if (!res.ok) throw new Error(`${path} failed (${res.status})`);
  return res.json();
}

export const uploadTitles = (file) => postFile('/upload/titles', file);
export const uploadTraits = (file) => postFile('/upload/traits', file);
export const uploadDeaths = (file) => postFile('/upload/deaths', file);
export const uploadNames = (file) => postFile('/upload/names', file);

export async function startGeneration(payload) {
  const res = await fetch(`${BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`generate failed (${res.status})`);
  return res.json();
}

export async function fetchStatus(taskId) {
  const res = await fetch(`${BASE}/status/${taskId}`);
  if (!res.ok) throw new Error(`status failed (${res.status})`);
  return res.json();
}

export const downloadUrl = (taskId) => `${BASE}/download/${taskId}`;
