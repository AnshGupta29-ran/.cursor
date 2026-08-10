// Simple API wrapper for the FastAPI backend
export const API_URL = "http://127.0.0.1:8000/api";

export async function seedDemo() {
  const resp = await fetch(`${API_URL}/demo/seed`);
  if (!resp.ok) throw new Error("Failed to seed demo");
  return resp.json();
}

export async function listExperiments() {
  const resp = await fetch(`${API_URL}/experiment`);
  if (!resp.ok) throw new Error("Failed to fetch experiments");
  return resp.json();
}

export async function getRun(runId) {
  const resp = await fetch(`${API_URL}/run/${runId}`);
  if (!resp.ok) throw new Error("Failed to fetch run");
  return resp.json();
}
