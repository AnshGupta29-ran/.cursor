const BASE = '/api';

async function req(method, path, body, raw = false) {
  const opts = { method, headers: {} };
  if (body !== undefined && !raw) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  } else if (body !== undefined && raw) {
    opts.body = body;
  }
  const res = await fetch(BASE + path, opts);
  const ct = res.headers.get('content-type') || '';
  const data = ct.includes('json') ? await res.json() : await res.text();
  if (!res.ok) {
    const e = (data && data.error) || { code: 'error', message: String(data) };
    const err = new Error(e.message);
    err.code = e.code;
    err.status = res.status;
    throw err;
  }
  return data;
}

export const api = {
  health: () => req('GET', '/health'),
  listExperiments: () => req('GET', '/experiments'),
  getExperiment: (id) => req('GET', `/experiments/${id}`),
  createExperiment: (name, gate_policy) => req('POST', '/experiments', { name, gate_policy }),
  setChampion: (expId, run_id, policy) => req('PUT', `/experiments/${expId}/champion`, { run_id, policy }),
  deleteRun: (expId, runId) => req('DELETE', `/experiments/${expId}/runs/${runId}`),
  startRun: (experiment_id, name, tags) => req('POST', '/runs', { experiment_id, name, tags }),
  logBatch: (runId, params, metrics) => req('POST', `/runs/${runId}/log-batch`, { params, metrics }),
  finishRun: (runId) => req('POST', `/runs/${runId}/finish`),
  failRun: (runId) => req('POST', `/runs/${runId}/fail`),
  getRun: (runId) => req('GET', `/runs/${runId}`),
  getVerdict: (runId) => req('GET', `/runs/${runId}/verdict`),
  getInfluence: (expId) => req('GET', `/experiments/${expId}/influence`),
  compare: (expId, runIds) => req('GET', `/experiments/${expId}/compare?run_ids=${runIds.join(',')}`),
  listArtifacts: (runId) => req('GET', `/runs/${runId}/artifacts`),
  previewArtifact: (aid) => req('GET', `/artifacts/${aid}/preview`),
  uploadArtifact: (runId, name, contentType, body) =>
    req('POST', `/runs/${runId}/artifacts?name=${encodeURIComponent(name)}&content_type=${encodeURIComponent(contentType)}`, body, true),
  getActivity: () => req('GET', '/activity'),
  seed: () => req('POST', '/demo/seed'),
};
