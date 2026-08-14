# Agente de Aplicación a Empleos

Plataforma multi-usuario: cada quien sube su CV y configura sus preferencias
(rol, ubicación, salario, remoto/presencial, etc.). El sistema trae vacantes
reales (Adzuna API), calcula un score de match CV↔vacante, y genera una
carta de presentación + resumen de CV ajustado para cada vacante. **No
aplica automáticamente en LinkedIn/Indeed/OCC** — eso viola sus Términos de
Servicio y arriesga las cuentas de tus usuarios. En vez de eso, deja todo
listo para que la persona revise y aplique con un clic desde el portal.

## Estructura

```
job-agent/
├── backend/     API en FastAPI + Postgres (Supabase)
└── frontend/    App en React (Vite)
```

## 1. Backend

### 1.1 Crear la base de datos en Supabase

1. Crea un proyecto gratis en https://supabase.com
2. Ve a **Project Settings → Database → Connection string** y copia la URI
   (modo "Session pooler" recomendado para evitar problemas de conexión).

### 1.2 Configurar y correr el backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edita `backend\.env` y llena:
- `DATABASE_URL` con la cadena de Supabase que copiaste
- `JWT_SECRET` con una cadena aleatoria larga (puedes generarla con `python -c "import secrets; print(secrets.token_hex(32))"`)
- `ADZUNA_APP_ID` y `ADZUNA_APP_KEY` — regístrate gratis en https://developer.adzuna.com/
- `ADZUNA_COUNTRY` (ej. `mx` para México, `us` para Estados Unidos)

Levanta el servidor:

```powershell
uvicorn app.main:app --reload --port 8000
```

Las tablas se crean automáticamente en Supabase al arrancar. Puedes probar
la API en `http://localhost:8000/docs` (documentación interactiva).

## 2. Frontend

```powershell
cd frontend
npm install
copy .env.example .env
```

Si tu backend corre en otra URL, ajusta `VITE_API_URL` en `frontend\.env`.

```powershell
npm run dev
```

Abre `http://localhost:5173`.

## 3. Flujo de uso

1. **Registro/Login** — cada usuario crea su cuenta.
2. **Mi perfil** — sube el CV (PDF o texto pegado) y configura preferencias
   (roles deseados, ubicación, salario mínimo, remoto, industrias, palabras
   a excluir).
3. **Vacantes** — busca por palabra clave (ej. "data analyst") y ubicación;
   trae resultados reales de Adzuna y los guarda en la base de datos
   compartida (útil para todos los usuarios de la plataforma).
4. **Matches** — calcula el score de similitud entre tu CV/preferencias y
   cada vacante guardada (filtra primero por reglas duras: remoto, salario,
   ubicación, palabras excluidas; luego calcula similitud de contenido).
5. **Aplicaciones** — genera carta de presentación + resumen de CV ajustado
   para cualquier match. Revisa, copia el texto, y aplica manualmente en el
   portal (LinkedIn/Indeed/OCC/sitio de la empresa). Marca como "enviada"
   para llevar registro.

## 4. Despliegue gratuito

- **Backend:** Render (free tier) — conecta el repo, build command
  `pip install -r requirements.txt`, start command
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- **Frontend:** Render Static Site o Vercel — build command `npm run build`,
  publish directory `dist`.
- **Base de datos:** Supabase (free tier, ya configurado arriba).

Recuerda actualizar `CORS_ORIGINS` en el backend y `VITE_API_URL` en el
frontend con las URLs reales una vez desplegado.

## 5. Extensiones posibles

- Cambiar el matching de TF-IDF a embeddings (OpenAI/Anthropic/Voyage) en
  `backend/app/services/matching.py` para mejor calidad semántica.
- Usar la API de Claude en `backend/app/services/tailoring.py` para generar
  cartas de presentación con mejor redacción (hoy usa un template simple).
- Agregar más fuentes de vacantes en `backend/app/services/job_sources.py`
  (USAJobs, RemoteOK, Jooble, o APIs oficiales de ATS como Greenhouse/Lever
  para aplicar directo donde la empresa lo permite).
