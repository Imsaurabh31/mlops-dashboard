/**
 * API client for the OLY VISION MLOps backend.
 * Base URL: http://localhost:8000/api
 *
 * All functions return parsed JSON or throw an Error with the
 * server's detail message.
 */

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

async function request(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);

  const res = await fetch(`${BASE}${path}`, opts);

  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const err = await res.json();
      detail = err.detail || detail;
    } catch { /* ignore parse error */ }
    throw new Error(detail);
  }

  // 204 No Content
  if (res.status === 204) return null;
  return res.json();
}

const get  = (path)        => request('GET',    path);
const post = (path, body)  => request('POST',   path, body);
const patch= (path, body)  => request('PATCH',  path, body);
const del  = (path)        => request('DELETE', path);

// ── Images ────────────────────────────────────────────────
export const imagesApi = {
  list:        (curated)  => get(`/images/${curated !== undefined ? `?curated=${curated}` : ''}`),
  get:         (id)       => get(`/images/${id}`),
  annotate:    (id, ann)  => post(`/images/${id}/annotate`, { image_id: id, annotations: ann }),
  stats:       ()         => get('/images/stats/summary'),
};

// ── Batches ───────────────────────────────────────────────
export const batchesApi = {
  list:        ()         => get('/batches/'),
  get:         (id)       => get(`/batches/${id}`),
  create:      (body)     => post('/batches/', body),
  update:      (id, body) => patch(`/batches/${id}`, body),
  delete:      (id)       => del(`/batches/${id}`),
  complete:    (id)       => post(`/batches/${id}/complete`),
};

// ── Training ──────────────────────────────────────────────
export const trainingApi = {
  listJobs:    ()         => get('/training/jobs'),
  getJob:      (id)       => get(`/training/jobs/${id}`),
  getLogs:     (id)       => get(`/training/jobs/${id}/logs`),
  trigger:     (body)     => post('/training/trigger', body),
  status:      ()         => get('/training/status'),
};
