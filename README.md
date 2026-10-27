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
  scripts/schema.sql          esquema SQL de las 18 tablas (+ trigger actualizado)
  scripts/  tests/  requirements.txt  runtime.txt  .env.example
frontend/                     SvelteKit
  src/lib/components/         Navbar, Header, Footer, Card, Boton, CampoFormulario, Mensaje, Insignia, SinDatos, Modal
  src/lib/services/           api_<modulo>.js (único lugar con fetch: api_base.js)
  src/routes/                 una carpeta por sección
aux_api/                      API auxiliar (Express + MySQL)
docs/                         documentos del proyecto
ia/                           prácticas de IA sobre la base del proyecto (solo lectura), ver ia/README.md
  docker-compose.yml          Práctica 1: Open WebUI en Docker + Ollama
  text_to_sql/                Práctica 3: text-to-SQL con Open WebUI + Ollama
  groq_mcp/                   Práctica 4: Groq + MCP Toolbox + mcpo
  ia_lectura.sql              usuario de Neon de solo lectura para la IA
```

Flujo del backend: **ruta → repositorio → Database**. La conexión usa las variables `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
y `DB_PORT` del `.env`, igual que la guía. Opcional: `DB_SSLMODE` (por ejemplo `require` para Neon); si no se define, no se envía.

**Base de datos ya existente en Neon:** pegar `backend/scripts/migracion_defaults.sql` en el SQL Editor de Neon
(valores por defecto de `usuario.activo`, `autorizacion_acudiente.vigente` e `inscripcion_estudiante.asistio`;
seguro y repetible).

## Ejecutar en el computador

**Backend** (desde `backend/`):

```
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env          # completa DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT y SECRET_KEY
uvicorn main:app --reload       # http://localhost:8000  ·  Swagger en /docs
```

Base nueva: `python -m scripts.inicializar_bd` (crea las tablas con `scripts/schema.sql` y los datos base) y luego
`python -m scripts.crear_admin` (también desde `backend/`).

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

## Rutas de la API principal (prefijo `/api/v1`)

Generadas de la app; la documentación interactiva está en `/docs`.

| Módulo | Método | Ruta |
|---|---|---|
| Catálogos | `GET` | `/catalogos/categorias` |
| Catálogos | `GET` | `/catalogos/ciudades` |
| Catálogos | `GET` | `/catalogos/grados` |
| Catálogos (CRUD admin) | `GET` | `/admin/catalogos/{tabla}` |
| Catálogos (CRUD admin) | `POST` | `/admin/catalogos/{tabla}` |
| Catálogos (CRUD admin) | `GET` | `/admin/catalogos/{tabla}/{registro_id}` |
| Catálogos (CRUD admin) | `PUT` | `/admin/catalogos/{tabla}/{registro_id}` |
| Catálogos (CRUD admin) | `DELETE` | `/admin/catalogos/{tabla}/{registro_id}` |
| Catálogos (CRUD admin) | `PATCH` | `/admin/catalogos/{tabla}/{registro_id}/estado` |
| Estudiantes (colegio) | `GET` | `/colegio/estudiantes` |
| Estudiantes (colegio) | `POST` | `/colegio/estudiantes` |
| Estudiantes (colegio) | `GET` | `/colegio/estudiantes/{estudiante_id}` |
| Estudiantes (colegio) | `PUT` | `/colegio/estudiantes/{estudiante_id}` |
| Estudiantes (colegio) | `DELETE` | `/colegio/estudiantes/{estudiante_id}` |
| Eventos (organizador) | `GET` | `/organizador/eventos` |
| Eventos (organizador) | `POST` | `/organizador/eventos` |
| Eventos (organizador) | `PUT` | `/organizador/eventos/{evento_id}` |
| Eventos (organizador) | `DELETE` | `/organizador/eventos/{evento_id}` |
| Eventos (organizador) | `POST` | `/organizador/eventos/{evento_id}/enviar` |
| Eventos (colegio) | `GET` | `/colegio/eventos` |
| Eventos (administrador) | `GET` | `/admin/eventos` |
| Eventos (administrador) | `POST` | `/admin/eventos/{evento_id}/cerrar` |
| Eventos (administrador) | `PATCH` | `/admin/eventos/{evento_id}/decision` |
| Inscripciones (organizador) | `GET` | `/organizador/inscripciones` |
| Inscripciones (organizador) | `PATCH` | `/organizador/inscripciones/{inscripcion_id}` |
| Inscripciones (organizador) | `GET` | `/organizador/eventos/{evento_id}/asistencia` |
| Inscripciones (organizador) | `PUT` | `/organizador/eventos/{evento_id}/asistencia` |
| Inscripciones (organizador) | `GET` | `/organizador/eventos/{evento_id}/reporte/colegios.csv` |
| Inscripciones (organizador) | `GET` | `/organizador/eventos/{evento_id}/reporte/estudiantes.csv` |
| Inscripciones (colegio) | `GET` | `/colegio/inscripciones` |
| Inscripciones (colegio) | `POST` | `/colegio/eventos/{evento_id}/inscripcion` |
| Usuarios y roles (administrador) | `GET` | `/admin/roles` |
| Usuarios y roles (administrador) | `GET` | `/admin/usuarios` |
| Usuarios y roles (administrador) | `POST` | `/admin/usuarios` |
| Usuarios y roles (administrador) | `PATCH` | `/admin/usuarios/{usuario_id}` |
| Usuarios y roles (administrador) | `DELETE` | `/admin/usuarios/{usuario_id}` |
| Usuarios y roles (administrador) | `PUT` | `/admin/roles/{rol_id}/modulos` |
| Usuarios y roles (administrador) | `PATCH` | `/admin/usuarios/{usuario_id}/estado` |
| Usuarios y roles (administrador) | `POST` | `/admin/usuarios/{usuario_id}/restablecer` |
| Colegios (organizador) | `GET` | `/organizador/colegios` |
| Colegios (organizador) | `POST` | `/organizador/colegios` |
| Colegios (organizador) | `DELETE` | `/organizador/colegios/{colegio_id}` |
| Colegios (organizador) | `PATCH` | `/organizador/colegios/{colegio_id}/activo` |
| Colegios (administrador) | `GET` | `/admin/colegios` |
| Organizadores (administrador) | `GET` | `/admin/organizadores` |
| Organizadores (administrador) | `PATCH` | `/admin/organizadores/{organizador_id}/activo` |
| Administrador | `GET` | `/admin/resumen` |
| Autenticación | `POST` | `/auth/cambiar-contrasena` |
| Autenticación | `POST` | `/auth/login` |
| Autenticación | `POST` | `/auth/logout` |
| Autenticación | `GET` | `/auth/me` |
| Autenticación | `POST` | `/auth/registro/organizador` |

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

## Mejoras futuras

- **Índices** (hoy solo existen los de llaves primarias y `UNIQUE`). Varias consultas filtran por columnas sin índice:
  `evento.id_organizador`, `evento.id_estado`, `inscripcion.id_colegio`, `colegio.id_organizador`, `usuario.id_rol`
  y `auditoria (tabla, registro_id)`. Con los volúmenes actuales no se nota; agregarlos si los datos crecen.
