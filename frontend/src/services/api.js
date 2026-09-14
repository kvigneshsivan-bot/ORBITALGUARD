const API = import.meta.env.VITE_API_URL || '/api'

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, { headers: { 'Content-Type': 'application/json' }, ...options })
  if (!response.ok) throw new Error((await response.json()).detail || 'API request failed')
  return response.json()
}
export const api = {
  satellites: () => request('/satellites'),
  telemetry: id => request(`/telemetry/${id}`),
  history: id => request(`/telemetry/${id}/history`),
  faults: () => request('/faults'),
  alerts: () => request('/alerts'),
  analytics: () => request('/analytics'),
  source: () => request('/source'),
  state: id => request(`/state?satellite_id=${encodeURIComponent(id)}`),
  simulate: (scenario, satelliteId) => request(`/simulation/${scenario}?satellite_id=${encodeURIComponent(satelliteId)}`, { method: 'POST' }),
  acknowledge: id => request(`/alerts/${id}/acknowledge`, { method: 'PATCH' })
}
