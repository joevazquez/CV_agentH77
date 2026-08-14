import { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function Jobs() {
  const [query, setQuery] = useState('')
  const [location, setLocation] = useState('')
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function loadJobs() {
    api.listJobs().then(setJobs).catch(() => {})
  }

  useEffect(() => { loadJobs() }, [])

  async function handleFetch(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await api.fetchJobs(query, location)
      loadJobs()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1>Vacantes</h1>
      <p className="muted">
        Trae vacantes reales desde Adzuna (requiere configurar ADZUNA_APP_ID / ADZUNA_APP_KEY en el backend).
      </p>

      <form onSubmit={handleFetch} className="card">
        <label>Palabra clave</label>
        <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="data analyst" required />

        <label>Ubicacion (opcional)</label>
        <input type="text" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Ciudad de Mexico" />

        {error && <div className="error">{error}</div>}
        <button className="primary" type="submit" disabled={loading}>
          {loading ? 'Buscando...' : 'Buscar vacantes'}
        </button>
      </form>

      <h2>Vacantes guardadas ({jobs.length})</h2>
      {jobs.map((job) => (
        <div className="card" key={job.id}>
          <strong>{job.title}</strong> — {job.company || 'Empresa no especificada'}
          <div className="muted">{job.location} {job.remote ? '· Remoto' : ''}</div>
          <p style={{ fontSize: 13 }}>{job.description.slice(0, 220)}...</p>
          <a href={job.url} target="_blank" rel="noreferrer" className="muted">Ver original →</a>
        </div>
      ))}
    </div>
  )
}
