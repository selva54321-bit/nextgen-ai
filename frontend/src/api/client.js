// Set VITE_API_BASE_URL in the deployment environment when the backend host changes.
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080').replace(/\/$/, '')

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options)
  const body = await response.text()
  let data
  try { data = body ? JSON.parse(body) : null } catch { data = body }
  if (!response.ok) throw new Error(data?.error || data?.message || `Request failed (${response.status})`)
  return data
}

function upload(path, file) {
  const form = new FormData()
  form.append('file', file)
  return request(path, { method: 'POST', body: form })
}

export const api = {
  warehouseUpload: file => upload('/api/v1/warehouse/upload', file),
  warehouseSimulation: () => request('/api/v1/warehouse/simulations', { method: 'POST' }),
  taskRanking: () => request('/api/v1/warehouse/picking/rank', { method: 'POST' }),
  dispatchPlan: payload => request('/api/v1/dispatch/plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
  dispatchBatch: file => upload('/api/v1/dispatch/plan-batch', file),
  stopRisk: stopId => request(`/api/v1/delivery/stops/${encodeURIComponent(stopId)}/risk`),
}
