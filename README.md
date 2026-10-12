# Conexión Escolar

Plataforma web para organizar eventos de colegios: los **organizadores** publican eventos, los **colegios** inscriben a sus estudiantes
(con autorización del acudiente) y el **administrador** aprueba eventos y gestiona usuarios, roles y módulos.

Este repositorio tiene **dos APIs**:

| Parte | Tecnología | Carpeta | Documentación interactiva |
|---|---|---|---|
| API principal + frontend | FastAPI · PostgreSQL (Neon) · SvelteKit | `app/`, `frontend/` | `/docs` (Swagger) |
| API auxiliar (PQRS, comunicados, valoraciones) | Express · MySQL | `aux_api/` | `/docs` (Swagger) |

## Parcial I: dónde está cada cosa

| Requerimiento | Dónde |
|---|---|
| BD PostgreSQL, 18 tablas normalizadas | `app/models.py` · script para Neon: `scripts/migracion_taller.sql` |
| PK, únicos, **estado**, **creado**, **actualizado** en todas las tablas | clase `Auditable` en `app/models.py` + trigger `trg_actualizado` en la migración |
| `rol`, `usuario`, `modulo`, `modulo_por_rol` | `app/models.py` (primeras 4 clases) |
| Estado manipulado desde la API (borrado lógico) | `DELETE` y `PATCH …/estado` en `/admin/usuarios` y `/admin/catalogos/{tabla}`; también colegios, eventos y estudiantes |
| API con endpoints (FastAPI) | `app/api/v1/endpoints/` · Swagger en `/docs` |
| JWT y validación | `app/core/security.py` (crear/verificar) y `app/api/deps.py` (validar en cada petición) |
| BD MySQL auxiliar, 4 tablas | `aux_api/schema.sql` |
| API Express con endpoints | `aux_api/src/routes/` · Swagger en `/docs` de la API auxiliar |
| Pruebas | `pytest -q` (API principal) · `cd aux_api && npm test` |

## Ejecutar la API principal

```
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # y completa DATABASE_URL y SECRET_KEY
uvicorn app.main:app --reload
```

Swagger: http://localhost:8000/docs · Para entrar: `POST /api/v1/auth/login` → copia `access_token` → botón **Authorize**.

**Base de datos ya existente en Neon:** pega `scripts/migracion_taller.sql` en el SQL Editor de Neon (es idempotente) **antes** de desplegar el código nuevo.

Primer administrador: `python -m scripts.crear_admin`.

## Despliegue (Render)

API principal: Web Service · Build `pip install -r requirements.txt` · Start `uvicorn app.main:app --host 0.0.0.0 --port $PORT` ·
variables `DATABASE_URL`, `SECRET_KEY`, `COOKIE_SECURE=true`, `FORZAR_HTTPS=true`, `FRONTEND_URL`.

API auxiliar: otro Web Service del mismo repositorio con **Root Directory `aux_api`** · Build `npm install` · Start `npm start` ·
variables `DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME DB_SSL`, `SECRET_KEY` (**la misma** de la API principal) y `CORS_ORIGINS`. Ver `aux_api/README.md`.
