import { Routes, Route, Link, Navigate, useNavigate } from 'react-router-dom'
import { api } from './api/client'
import logo from './assets/logo.png'
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
        <Link to={loggedIn ? '/profile' : '/login'} className="brand">
          <img src={logo} alt="CV_agent H77" />
          <span className="brand-text">
            <span className="brand-name">CV_AGENT H77</span>
            <span className="brand-tagline">Buscando empleo, impulsando tu futuro</span>
          </span>
        </Link>
        {loggedIn && (
          <>
            <Link to="/profile">Mi perfil</Link>
            <Link to="/jobs">Buscar empleo</Link>
            <Link to="/applications">Mis aplicaciones</Link>
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
