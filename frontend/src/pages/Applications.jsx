import { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function Applications() {
  const [apps, setApps] = useState([])
  const [error, setError] = useState('')

  function loadApps() {
    api.listApplications().then(setApps).catch((err) => setError(err.message))
  }

  useEffect(() => { loadApps() }, [])

  async function markSubmitted(id) {
    try {
      await api.markSubmitted(id)
      loadApps()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div>
      <h1>Aplicaciones generadas</h1>
      <p className="muted">
        Aqui se guarda la carta y el resumen de CV que el agente generó para cada vacante. Revisalos, ajusta lo que
        quieras, y aplica manualmente en el portal correspondiente (LinkedIn / Indeed / OCC). Cuando lo hagas, marca
        la aplicacion como enviada.
      </p>
      {error && <div className="error">{error}</div>}

      {apps.map((app) => (
        <div className="card" key={app.id}>
          <div className="muted">Vacante ID: {app.job_id}</div>
          {app.submitted_by_user ? (
            <span className="score-badge">Ya aplicada</span>
          ) : (
            <button className="secondary" onClick={() => markSubmitted(app.id)}>
              Marcar como enviada
            </button>
          )}

          <h3>Carta de presentacion</h3>
          <pre>{app.cover_letter}</pre>

          <h3>Resumen de CV ajustado</h3>
          <pre>{app.tailored_cv}</pre>
        </div>
      ))}

      {apps.length === 0 && <p className="muted">Aun no has generado ninguna aplicacion. Ve a "Matches" y genera una.</p>}
    </div>
  )
}
