import { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function Profile() {
  const [cvText, setCvText] = useState('')
  const [skills, setSkills] = useState('')
  const [summary, setSummary] = useState('')
  const [cvSaving, setCvSaving] = useState(false)
  const [cvMsg, setCvMsg] = useState('')

  const [prefs, setPrefs] = useState({
    desired_roles: '',
    locations: '',
    remote_only: false,
    min_salary: '',
    industries: '',
    seniority: '',
    keywords_exclude: '',
  })
  const [prefsSaving, setPrefsSaving] = useState(false)
  const [prefsMsg, setPrefsMsg] = useState('')

  const [experiences, setExperiences] = useState([])
  const [expForm, setExpForm] = useState({
    job_title: '', company: '', location: '', start_period: '', end_period: '', description: '',
  })
  const [expSaving, setExpSaving] = useState(false)
  const [expMsg, setExpMsg] = useState('')
  const [regenerating, setRegenerating] = useState(false)
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    api.getCV().then((cv) => {
      setCvText(cv.raw_text || '')
      setSkills((cv.skills || []).join(', '))
      setSummary(cv.summary || '')
    }).catch(() => {})

    api.getPreferences().then((p) => {
      setPrefs({
        desired_roles: (p.desired_roles || []).join(', '),
        locations: (p.locations || []).join(', '),
        remote_only: p.remote_only,
        min_salary: p.min_salary ?? '',
        industries: (p.industries || []).join(', '),
        seniority: p.seniority || '',
        keywords_exclude: (p.keywords_exclude || []).join(', '),
      })
    }).catch(() => {})

    loadExperiences()
  }, [])

  function loadExperiences() {
    api.listExperience().then(setExperiences).catch(() => {})
  }

  function toList(str) {
    return str.split(',').map((s) => s.trim()).filter(Boolean)
  }

  async function saveCV(e) {
    e.preventDefault()
    setCvSaving(true)
    setCvMsg('')
    try {
      await api.saveCV({ raw_text: cvText, skills: toList(skills), summary })
      setCvMsg('CV guardado correctamente.')
    } catch (err) {
      setCvMsg(err.message)
    } finally {
      setCvSaving(false)
    }
  }

  async function uploadPdf(e) {
    const file = e.target.files[0]
    if (!file) return
    setCvSaving(true)
    setCvMsg('')
    try {
      const cv = await api.uploadCVFile(file)
      setCvText(cv.raw_text || '')
      setCvMsg('CV extraido del PDF y guardado.')
    } catch (err) {
      setCvMsg(err.message)
    } finally {
      setCvSaving(false)
    }
  }

  async function addExperience(e) {
    e.preventDefault()
    setExpSaving(true)
    setExpMsg('')
    try {
      await api.addExperience({
        ...expForm,
        end_period: expForm.end_period || null,
      })
      setExpForm({ job_title: '', company: '', location: '', start_period: '', end_period: '', description: '' })
      loadExperiences()
      setExpMsg('Experiencia agregada.')
    } catch (err) {
      setExpMsg(err.message)
    } finally {
      setExpSaving(false)
    }
  }

  async function removeExperience(id) {
    try {
      await api.deleteExperience(id)
      loadExperiences()
    } catch (err) {
      setExpMsg(err.message)
    }
  }

  async function handleRegenerateCV() {
    setRegenerating(true)
    setExpMsg('')
    try {
      const cv = await api.regenerateCV()
      setCvText(cv.raw_text || '')
      setExpMsg('Tu CV se actualizo con tu experiencia laboral.')
    } catch (err) {
      setExpMsg(err.message)
    } finally {
      setRegenerating(false)
    }
  }

  async function handleDownloadPdf() {
    setDownloading(true)
    setExpMsg('')
    try {
      await api.downloadCVPdf()
    } catch (err) {
      setExpMsg(err.message)
    } finally {
      setDownloading(false)
    }
  }

  async function savePrefs(e) {
    e.preventDefault()
    setPrefsSaving(true)
    setPrefsMsg('')
    try {
      await api.savePreferences({
        desired_roles: toList(prefs.desired_roles),
        locations: toList(prefs.locations),
        remote_only: prefs.remote_only,
        min_salary: prefs.min_salary === '' ? null : Number(prefs.min_salary),
        industries: toList(prefs.industries),
        seniority: prefs.seniority || null,
        keywords_exclude: toList(prefs.keywords_exclude),
      })
      setPrefsMsg('Preferencias guardadas.')
    } catch (err) {
      setPrefsMsg(err.message)
    } finally {
      setPrefsSaving(false)
    }
  }

  return (
    <div>
      <h1>Mi perfil</h1>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>CV</h2>
        <label>Subir CV en PDF (se extrae el texto automaticamente)</label>
        <input type="file" accept="application/pdf" onChange={uploadPdf} disabled={cvSaving} />

        <form onSubmit={saveCV}>
          <label>O pega el texto de tu CV directamente</label>
          <textarea value={cvText} onChange={(e) => setCvText(e.target.value)} placeholder="Pega aqui tu experiencia, educacion, etc." />

          <label>Habilidades (separadas por coma)</label>
          <input type="text" value={skills} onChange={(e) => setSkills(e.target.value)} placeholder="python, sql, liderazgo de equipos" />

          <label>Resumen profesional (opcional)</label>
          <textarea value={summary} onChange={(e) => setSummary(e.target.value)} placeholder="2-3 lineas sobre tu perfil" />

          {cvMsg && <div className="muted">{cvMsg}</div>}
          <button className="primary" type="submit" disabled={cvSaving}>
            {cvSaving ? 'Guardando...' : 'Guardar CV'}
          </button>
        </form>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>¿Quieres actualizar tu CV?</h2>
        <p className="muted" style={{ fontSize: 13 }}>
          Agrega cada trabajo que has tenido y el agente arma tu CV automaticamente. Puedes descargarlo en PDF cuando quieras.
        </p>

        <form onSubmit={addExperience}>
          <label>Titulo del puesto</label>
          <input type="text" value={expForm.job_title} onChange={(e) => setExpForm({ ...expForm, job_title: e.target.value })} placeholder="ej. Analista de Datos" required />

          <label>Empresa / lugar donde trabajaste</label>
          <input type="text" value={expForm.company} onChange={(e) => setExpForm({ ...expForm, company: e.target.value })} placeholder="ej. Banamex" required />

          <label>Ubicacion (opcional)</label>
          <input type="text" value={expForm.location} onChange={(e) => setExpForm({ ...expForm, location: e.target.value })} placeholder="ej. Ciudad de Mexico" />

          <label>Periodo - inicio</label>
          <input type="text" value={expForm.start_period} onChange={(e) => setExpForm({ ...expForm, start_period: e.target.value })} placeholder="ej. Enero 2022" required />

          <label>Periodo - fin (dejalo vacio si sigues ahi)</label>
          <input type="text" value={expForm.end_period} onChange={(e) => setExpForm({ ...expForm, end_period: e.target.value })} placeholder="ej. Diciembre 2023" />

          <label>Caracteristicas generales / logros</label>
          <textarea value={expForm.description} onChange={(e) => setExpForm({ ...expForm, description: e.target.value })} placeholder="Describe tus responsabilidades y logros principales en este puesto" required />

          <button className="primary" type="submit" disabled={expSaving}>
            {expSaving ? 'Agregando...' : 'Agregar experiencia'}
          </button>
        </form>

        {experiences.length > 0 && (
          <div style={{ marginTop: 20 }}>
            <h3 style={{ marginBottom: 8 }}>Tu experiencia guardada</h3>
            {experiences.map((exp) => (
              <div key={exp.id} className="card" style={{ marginTop: 8 }}>
                <strong>{exp.job_title}</strong> — {exp.company} {exp.location ? `· ${exp.location}` : ''}
                <div className="muted" style={{ fontSize: 12 }}>{exp.start_period} - {exp.end_period || 'Actualidad'}</div>
                <p style={{ fontSize: 13 }}>{exp.description}</p>
                <button className="secondary" onClick={() => removeExperience(exp.id)}>Eliminar</button>
              </div>
            ))}
          </div>
        )}

        {expMsg && <div className="muted" style={{ marginTop: 12 }}>{expMsg}</div>}

        <div style={{ display: 'flex', gap: 10, marginTop: 16, flexWrap: 'wrap' }}>
          <button className="primary" onClick={handleRegenerateCV} disabled={regenerating || experiences.length === 0}>
            {regenerating ? 'Actualizando...' : 'Actualizar mi CV con esta experiencia'}
          </button>
          <button className="secondary" onClick={handleDownloadPdf} disabled={downloading}>
            {downloading ? 'Descargando...' : 'Descargar mi CV en PDF'}
          </button>
        </div>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Mis preferencias</h2>
        <form onSubmit={savePrefs}>
          <label>Roles deseados (separados por coma)</label>
          <input type="text" value={prefs.desired_roles} onChange={(e) => setPrefs({ ...prefs, desired_roles: e.target.value })} placeholder="Data Analyst, Backend Developer" />

          <label>Ubicaciones aceptadas (separadas por coma)</label>
          <input type="text" value={prefs.locations} onChange={(e) => setPrefs({ ...prefs, locations: e.target.value })} placeholder="Ciudad de Mexico, Remoto" />

          <label>
            <input
              type="checkbox"
              checked={prefs.remote_only}
              onChange={(e) => setPrefs({ ...prefs, remote_only: e.target.checked })}
              style={{ width: 'auto', display: 'inline-block', marginRight: 8 }}
            />
            Solo trabajo remoto
          </label>

          <label>Salario minimo esperado (opcional)</label>
          <input type="number" value={prefs.min_salary} onChange={(e) => setPrefs({ ...prefs, min_salary: e.target.value })} placeholder="25000" />

          <label>Industrias de interes (separadas por coma)</label>
          <input type="text" value={prefs.industries} onChange={(e) => setPrefs({ ...prefs, industries: e.target.value })} placeholder="fintech, e-commerce" />

          <label>Nivel de experiencia</label>
          <select value={prefs.seniority} onChange={(e) => setPrefs({ ...prefs, seniority: e.target.value })}>
            <option value="">Sin especificar</option>
            <option value="junior">Junior</option>
            <option value="mid">Semi-senior</option>
            <option value="senior">Senior</option>
          </select>

          <label>Palabras que descartan una vacante (separadas por coma)</label>
          <input type="text" value={prefs.keywords_exclude} onChange={(e) => setPrefs({ ...prefs, keywords_exclude: e.target.value })} placeholder="ventas puerta a puerta, comision only" />

          {prefsMsg && <div className="muted">{prefsMsg}</div>}
          <button className="primary" type="submit" disabled={prefsSaving}>
            {prefsSaving ? 'Guardando...' : 'Guardar preferencias'}
          </button>
        </form>
      </div>
    </div>
  )
}
