# Conexión Escolar

Plataforma web para organizar eventos de colegios: los **organizadores** publican eventos, los **colegios** inscriben a sus estudiantes
(con autorización del acudiente) y el **administrador** aprueba eventos y gestiona usuarios, roles y módulos.

## Estructura (según la guía del profesor Bryan Fernandez)

```
backend/                      API principal (FastAPI + PostgreSQL)
  main.py                     crea la app y conecta cada módulo (include_router)
  app/core/database.py        clase Database.get_connection()  (psycopg2 + RealDictCursor)
  app/models/<modulo>.py      modelos Pydantic, uno por módulo
  app/repositories/<modulo>_repo.py   SQL puro con %s
  app/api/rutas_<modulo>.py   APIRouter de cada módulo
  app/frontend_dist/          frontend compilado que sirve FastAPI en producción
  scripts/  tests/  requirements.txt  runtime.txt  .env.example
frontend/                     SvelteKit
  src/lib/components/         Navbar, Header, Footer, Card, Boton, CampoFormulario, Mensaje, Insignia, SinDatos, Modal
  src/lib/services/           api_<modulo>.js (único lugar con fetch: api_base.js)
  src/routes/                 una carpeta por sección
aux_api/                      API auxiliar (Express + MySQL)
docs/                         documentos del proyecto
practica_1_docker/  practica_3_openwebui_postgres/  practica_4_groq_mcp_toolbox/   prácticas del curso
```

Flujo del backend: **ruta → repositorio → Database**. La conexión usa las variables `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
y `DB_PORT` del `.env`, igual que la guía. Opcional: `DB_SSLMODE` (por ejemplo `require` para Neon); si no se define, no se envía.

## Ejecutar en el computador

**Backend** (desde `backend/`):

```
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env          # completa DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT y SECRET_KEY
uvicorn main:app --reload       # http://localhost:8000  ·  Swagger en /docs
```

Base nueva: `python -m scripts.inicializar_bd` y luego `python -m scripts.crear_admin` (también desde `backend/`).

**Frontend** (desde `frontend/`, con el backend corriendo):

```
cd frontend
npm install
npm run dev                     # http://localhost:5173  (/api se reenvía al puerto 8000)
```

**Pruebas** (desde `backend/`, con una base PostgreSQL **de prueba**, nunca Neon: se borra en cada corrida):

```
set TEST_DATABASE_URL=postgresql://postgres@localhost:5432/pruebas
python -m pytest tests -q
```

## Publicar el frontend en el backend

FastAPI sirve el frontend compilado desde `backend/app/frontend_dist`. Después de cambiar el frontend:

```
cd frontend
npm run build
# reemplazar el contenido de backend/app/frontend_dist por el de frontend/build
```

## Despliegue (Render)

API principal: Web Service del repositorio con:

| Campo | Valor |
|---|---|
| Root Directory | `backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port 10000` |
| Variables | `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`, (opcional `DB_SSLMODE=require`), `SECRET_KEY`, `COOKIE_SECURE=true`, `FORZAR_HTTPS=true`, `FRONTEND_URL` |

(10000 es el puerto que Render usa por defecto.)

API auxiliar: otro Web Service del mismo repositorio con **Root Directory `aux_api`** · Build `npm install` · Start `npm start` ·
variables `DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME DB_SSL`, `SECRET_KEY` (**la misma** de la API principal) y `CORS_ORIGINS`. Ver `aux_api/README.md`.
