import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export default function Matches() {
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [creatingId, setCreatingId] = useState(null)
  const navigate = useNavigate()

  function loadMatches() {
    api.listMatches().then(setMatches).catch(() => {})
  }

  useEffect(() => { loadMatches() }, [])

  async function handleRefresh() {
    setLoading(true)
    setError('')
    try {
      await api.refreshMatches()
      loadMatches()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleCreateApplication(matchId) {
    setCreatingId(matchId)
    try {
      await api.createApplication(matchId)
      navigate('/applications')
    } catch (err) {
      setError(err.message)
    } finally {
      setCreatingId(null)
    }
  }

  return (
    <div>
      <h1>Tus matches</h1>
      <p className="muted">Compara tu CV y preferencias contra las vacantes guardadas.</p>
      <button className="primary" onClick={handleRefresh} disabled={loading}>
        {loading ? 'Calculando...' : 'Recalcular matches'}
      </button>
      {error && <div className="error">{error}</div>}

      {matches.map((m) => (
        <div className="card" key={m.id}>
          <span className="score-badge">{Math.round(m.score * 100)}% match</span>
          <h3 style={{ marginBottom: 4 }}>{m.job.title}</h3>
          <div className="muted">{m.job.company} — {m.job.location} {m.job.remote ? '· Remoto' : ''}</div>
          <p style={{ fontSize: 13 }}>{m.explanation}</p>
          <button className="secondary" onClick={() => handleCreateApplication(m.id)} disabled={creatingId === m.id}>
            {creatingId === m.id ? 'Generando...' : 'Generar carta + CV ajustado'}
          </button>
        </div>
      ))}

      {matches.length === 0 && !loading && (
        <p className="muted">Aun no hay matches. Sube tu CV, configura preferencias, trae vacantes y da clic en "Recalcular matches".</p>
      )}
    </div>
  )
}
