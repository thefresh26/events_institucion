# Conexión Escolar

Plataforma web para organizar eventos de colegios: los **organizadores** publican eventos, los **colegios** inscriben a sus estudiantes
(con autorización del acudiente) y el **administrador** aprueba eventos y gestiona usuarios, roles y módulos.

## Estructura (según la guía del profesor Bryan Fernandez)

```
backend/                      API principal (FastAPI + PostgreSQL)
  main.py                     crea la app y conecta cada módulo (include_router)
  app/core/database.py        clase Database.get_connection()  (psycopg 3)
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

Flujo del backend: **ruta → repositorio → Database**. Diferencias con la guía: se usa **psycopg 3** (no psycopg2) y una sola variable
**`DATABASE_URL`** (en vez de `DB_HOST`, `DB_NAME`, …).

## Ejecutar en el computador

**Backend** (desde `backend/`):

```
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env          # completa DATABASE_URL y SECRET_KEY
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

API principal: Web Service · **Root Directory `backend`** · Build `pip install -r requirements.txt` ·
Start `uvicorn main:app --host 0.0.0.0 --port $PORT` · variables `DATABASE_URL`, `SECRET_KEY`, `COOKIE_SECURE=true`,
`FORZAR_HTTPS=true`, `FRONTEND_URL`.

API auxiliar: otro Web Service del mismo repositorio con **Root Directory `aux_api`** · Build `npm install` · Start `npm start` ·
variables `DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME DB_SSL`, `SECRET_KEY` (**la misma** de la API principal) y `CORS_ORIGINS`. Ver `aux_api/README.md`.
