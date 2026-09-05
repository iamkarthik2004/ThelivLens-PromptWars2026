const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || 'ThelivLens could not complete the analysis. Please try again.');
  return body;
}

// This module is the only frontend boundary to the FastAPI service.
export async function analyzeMedia(file) {
  const form = new FormData();
  form.append('file', file);
  return request('/analyze/upload', { method: 'POST', body: form });
}
export async function analyzeUrl(url) { return request('/analyze/url', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url }) }); }
export async function verifyClaim(claim) { return request('/analyze/claim', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ claim }) }); }
export async function getAnalysis(id) { return request(`/analyze/${id}`); }
export async function getRecentAnalyses() { return request('/analyze'); }
export async function getSourceTrace(id) { return request(`/analyze/${id}/source-trace`); }
export async function askCopilot(question, analysis_context = {}) { return request('/analyze/copilot', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question, analysis_context }) }); }
