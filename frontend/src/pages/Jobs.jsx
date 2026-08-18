import { useState } from 'react'
import { api } from '../api/client'

export default function Jobs() {
  const [query, setQuery] = useState('')
  const [location, setLocation] = useState('')
  const [salaryMin, setSalaryMin] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [autoLoading, setAutoLoading] = useState(false)
  const [error, setError] = useState('')
  const [generatingId, setGeneratingId] = useState(null)
  const [applications, setApplications] = useState({}) // job_id -> application

  // -- vacante manual (pegada desde otro sitio) --
  const [manualTitle, setManualTitle] = useState('')
  const [manualCompany, setManualCompany] = useState('')
  const [manualLocation, setManualLocation] = useState('')
  const [manualUrl, setManualUrl] = useState('')
  const [manualDescription, setManualDescription] = useState('')
  const [manualLoading, setManualLoading] = useState(false)
  const [manualError, setManualError] = useState('')
  const [manualResult, setManualResult] = useState(null) // { job, application }

  async function handleSearch(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResults([])
    try {
      const data = await api.searchJobs(query, location, salaryMin || null)
      setResults(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleAutoSearch() {
    setAutoLoading(true)
    setError('')
    setResults([])
    try {
      const prefs = await api.getPreferences()
      if (!prefs.desired_roles || prefs.desired_roles.length === 0) {
        setError('Primero agrega al menos un "rol deseado" en Mi perfil.')
        return
      }
      const loc = prefs.locations && prefs.locations.length > 0 ? prefs.locations[0] : null
      const allResults = []
      const seenIds = new Set()
      for (const role of prefs.desired_roles) {
        const data = await api.searchJobs(role, loc, prefs.min_salary || null)
        for (const job of data) {
          if (!seenIds.has(job.id)) {
            seenIds.add(job.id)
            allResults.push(job)
          }
        }
      }
      setResults(allResults)
    } catch (err) {
      setError(err.message)
    } finally {
      setAutoLoading(false)
    }
  }

  async function handleImproveCV(jobId) {
    setGeneratingId(jobId)
    setError('')
    try {
      const application = await api.createApplicationFromJob(jobId)
      setApplications((prev) => ({ ...prev, [jobId]: application }))
    } catch (err) {
      setError(err.message)
    } finally {
      setGeneratingId(null)
    }
  }

  async function handleManualSubmit(e) {
    e.preventDefault()
    setManualLoading(true)
    setManualError('')
    setManualResult(null)
    try {
      const job = await api.createManualJob({
        title: manualTitle,
        company: manualCompany || null,
        location: manualLocation || null,
        url: manualUrl || null,
        description: manualDescription,
      })
      const application = await api.createApplicationFromJob(job.id)
      setManualResult({ job, application })
      setManualTitle('')
      setManualCompany('')
      setManualLocation('')
      setManualUrl('')
      setManualDescription('')
    } catch (err) {
      setManualError(err.message)
    } finally {
      setManualLoading(false)
    }
  }

  return (
    <div>
      <h1>Buscar empleo</h1>
      <p className="muted">
        Escribe el puesto que buscas y tu sueldo esperado. El agente trae vacantes reales, las compara contra tu CV
        guardado, y por cada una te puede generar tu CV mejorado y carta de presentacion.
      </p>

      <form onSubmit={handleSearch} className="card">
        <label>Puesto o palabra clave</label>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="ej. analista de datos, contador, backend developer"
          required
        />

        <label>Ubicacion (opcional)</label>
        <input type="text" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Ciudad de Mexico" />

        <label>Sueldo minimo esperado (opcional)</label>
        <input type="number" value={salaryMin} onChange={(e) => setSalaryMin(e.target.value)} placeholder="25000" />

        {error && <div className="error">{error}</div>}
        <button className="primary" type="submit" disabled={loading}>
          {loading ? 'Buscando...' : 'Buscar'}
        </button>
      </form>

      <p className="muted" style={{ marginTop: 20, fontSize: 13 }}>
        ¿No quieres escribir nada? Usa tus roles guardados en Mi perfil:
      </p>
      <button className="secondary" onClick={handleAutoSearch} disabled={autoLoading}>
        {autoLoading ? 'Buscando segun tus preferencias...' : '🔍 Buscar automatico segun mis preferencias'}
      </button>

      {results.length > 0 && (
        <h2>Resultados ({results.length})</h2>
      )}

      {results
        .slice()
        .sort((a, b) => b.score - a.score)
        .map((job) => {
          const application = applications[job.id]
          return (
            <div className="card" key={job.id}>
              <span className="score-badge">{Math.round(job.score * 100)}% match</span>
              <h3 style={{ marginBottom: 4 }}>{job.title}</h3>
              <div className="muted">
                {job.company} — {job.location} {job.remote ? '· Remoto' : ''}
                {job.salary_min ? ` · desde $${job.salary_min.toLocaleString()}` : ''}
              </div>
              <p style={{ fontSize: 13 }}>{job.description.slice(0, 220)}...</p>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                <a href={job.url} target="_blank" rel="noreferrer" className="muted">Ver original →</a>
                <button className="secondary" onClick={() => handleImproveCV(job.id)} disabled={generatingId === job.id}>
                  {generatingId === job.id ? 'Generando...' : 'Mejorar mi CV para esta vacante'}
                </button>
              </div>

              {application && (
                <div style={{ marginTop: 14 }}>
                  <h4 style={{ marginBottom: 4 }}>Tu CV mejorado para esta vacante</h4>
                  <pre>{application.tailored_cv}</pre>
                  <h4 style={{ marginBottom: 4 }}>Carta de presentacion sugerida</h4>
                  <pre>{application.cover_letter}</pre>
                  <p className="muted" style={{ fontSize: 12 }}>
                    Revisa y ajusta el texto a tu gusto antes de aplicar manualmente en el portal.
                  </p>
                </div>
              )}
            </div>
          )
        })}

      {!loading && results.length === 0 && (
        <p className="muted">Escribe un puesto arriba y dale "Buscar" para ver vacantes.</p>
      )}

      <h2>¿Viste una vacante en otro sitio?</h2>
      <p className="muted">
        Si encontraste algo en OCC, LinkedIn, Indeed o en el sitio de la empresa, pega aqui el link (para
        recordar de donde es) y copia/pega la descripcion del puesto. El agente te genera tu CV mejorado y carta
        de presentacion para esa vacante especifica, igual que con las de arriba.
      </p>

      <form onSubmit={handleManualSubmit} className="card">
        <label>Puesto</label>
        <input type="text" value={manualTitle} onChange={(e) => setManualTitle(e.target.value)} required placeholder="ej. Analista Financiero" />

        <label>Empresa (opcional)</label>
        <input type="text" value={manualCompany} onChange={(e) => setManualCompany(e.target.value)} />

        <label>Ubicacion (opcional)</label>
        <input type="text" value={manualLocation} onChange={(e) => setManualLocation(e.target.value)} />

        <label>Link de la vacante (opcional, solo como referencia)</label>
        <input type="text" value={manualUrl} onChange={(e) => setManualUrl(e.target.value)} placeholder="https://..." />

        <label>Descripcion del puesto (copia y pega el texto completo)</label>
        <textarea
          value={manualDescription}
          onChange={(e) => setManualDescription(e.target.value)}
          required
          placeholder="Pega aqui la descripcion, requisitos y responsabilidades de la vacante"
        />

        {manualError && <div className="error">{manualError}</div>}
        <button className="primary" type="submit" disabled={manualLoading}>
          {manualLoading ? 'Generando...' : 'Generar mi CV y carta para esta vacante'}
        </button>
      </form>

      {manualResult && (
        <div className="card">
          <h3 style={{ marginBottom: 4 }}>{manualResult.job.title}</h3>
          <div className="muted">{manualResult.job.company} — {manualResult.job.location}</div>
          {manualResult.job.url && (
            <a href={manualResult.job.url} target="_blank" rel="noreferrer" className="muted">Ver vacante original →</a>
          )}
          <h4 style={{ marginBottom: 4, marginTop: 14 }}>Tu CV mejorado para esta vacante</h4>
          <pre>{manualResult.application.tailored_cv}</pre>
          <h4 style={{ marginBottom: 4 }}>Carta de presentacion sugerida</h4>
          <pre>{manualResult.application.cover_letter}</pre>
          <p className="muted" style={{ fontSize: 12 }}>
            Tambien la puedes ver despues en la pestaña "Aplicaciones".
          </p>
        </div>
      )}
    </div>
  )
}
