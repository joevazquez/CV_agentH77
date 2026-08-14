import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { api } from '../api/client'

export default function Register() {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.register({ email, password, full_name: fullName })
      const res = await api.login({ email, password })
      api.setToken(res.access_token)
      navigate('/profile')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1>Crear cuenta</h1>
      <form onSubmit={handleSubmit}>
        <label>Nombre completo</label>
        <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} required />

        <label>Correo</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />

        <label>Contrasena</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />

        {error && <div className="error">{error}</div>}
        <button className="primary" type="submit" disabled={loading}>
          {loading ? 'Creando...' : 'Crear cuenta'}
        </button>
      </form>
      <p className="muted">
        ¿Ya tienes cuenta? <Link to="/login">Inicia sesion</Link>
      </p>
    </div>
  )
}
