const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function getToken() {
  return localStorage.getItem('token')
}

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (auth) {
    const token = getToken()
    if (token) headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    let detail = 'Error en la solicitud'
    try {
      const data = await res.json()
      detail = data.detail || detail
    } catch (_) {}
    throw new Error(detail)
  }

  if (res.status === 204) return null
  return res.json()
}

export const api = {
  register: (payload) => request('/auth/register', { method: 'POST', body: payload, auth: false }),
  login: (payload) => request('/auth/login', { method: 'POST', body: payload, auth: false }),
  me: () => request('/auth/me'),

  getCV: () => request('/cv'),
  saveCV: (payload) => request('/cv', { method: 'PUT', body: payload }),
  uploadCVFile: async (file) => {
    const token = getToken()
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${API_URL}/cv/upload-pdf`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error(data.detail || 'No se pudo subir el CV')
    }
    return res.json()
  },

  getPreferences: () => request('/preferences'),
  savePreferences: (payload) => request('/preferences', { method: 'PUT', body: payload }),

  fetchJobs: (query, location) =>
    request(`/jobs/fetch?query=${encodeURIComponent(query)}${location ? `&location=${encodeURIComponent(location)}` : ''}`, {
      method: 'POST',
    }),
  listJobs: () => request('/jobs'),

  refreshMatches: () => request('/matches/refresh', { method: 'POST' }),
  listMatches: () => request('/matches'),

  createApplication: (matchId) => request(`/applications/from-match/${matchId}`, { method: 'POST' }),
  listApplications: () => request('/applications'),
  markSubmitted: (appId) => request(`/applications/${appId}/submitted`, { method: 'PATCH', body: { submitted_by_user: true } }),

  setToken: (token) => localStorage.setItem('token', token),
  clearToken: () => localStorage.removeItem('token'),
  hasToken: () => !!getToken(),
}
