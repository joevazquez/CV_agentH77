import { Routes, Route, Link, Navigate, useNavigate } from 'react-router-dom'
import { api } from './api/client'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import Profile from './pages/Profile.jsx'
import Jobs from './pages/Jobs.jsx'
import Matches from './pages/Matches.jsx'
import Applications from './pages/Applications.jsx'

function RequireAuth({ children }) {
  if (!api.hasToken()) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  const navigate = useNavigate()
  const loggedIn = api.hasToken()

  function logout() {
    api.clearToken()
    navigate('/login')
  }

  return (
    <div>
      <nav>
        <span className="brand">🤖 Agente de Empleo</span>
        {loggedIn && (
          <>
            <Link to="/profile">Mi perfil</Link>
            <Link to="/jobs">Vacantes</Link>
            <Link to="/matches">Matches</Link>
            <Link to="/applications">Aplicaciones</Link>
            <button onClick={logout}>Cerrar sesion</button>
          </>
        )}
        {!loggedIn && (
          <>
            <Link to="/login">Entrar</Link>
            <Link to="/register">Registrarse</Link>
          </>
        )}
      </nav>

      <div className="container">
        <Routes>
          <Route path="/" element={<Navigate to={loggedIn ? '/profile' : '/login'} replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/profile" element={<RequireAuth><Profile /></RequireAuth>} />
          <Route path="/jobs" element={<RequireAuth><Jobs /></RequireAuth>} />
          <Route path="/matches" element={<RequireAuth><Matches /></RequireAuth>} />
          <Route path="/applications" element={<RequireAuth><Applications /></RequireAuth>} />
        </Routes>
      </div>
    </div>
  )
}
