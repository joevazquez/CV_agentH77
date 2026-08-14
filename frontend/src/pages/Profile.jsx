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
  }, [])

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
