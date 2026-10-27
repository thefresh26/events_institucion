# API auxiliar de Conexión Escolar (Express + MySQL)

PQRS, comunicados y valoraciones de eventos. Valida **los mismos JWT** que la API principal (FastAPI): mismo `SECRET_KEY`, algoritmo HS256,
claims `sub` (id de usuario) y `rol`.

## Base de datos (MySQL) — `schema.sql`

| Tabla | PK | Únicos | FK |
|---|---|---|---|
| `tipo_pqrs` | id | nombre | — |
| `pqrs` | id | radicado | id_tipo → tipo_pqrs |
| `comunicado` | id | slug | — |
| `valoracion_evento` | id | (id_evento, id_usuario) | — |

Todas con `estado` (1 activo / 0 eliminado: el registro no se borra), `creado` y `actualizado` (`ON UPDATE CURRENT_TIMESTAMP`).

## Ejecutar

```
cd aux_api
npm install
copy .env.example .env     # completa DB_* y SECRET_KEY (igual a la API principal)
npm run init-db            # crea las tablas
npm start                  # http://localhost:4000/docs
```

## Endpoints (prefijo `/api/aux`)

| Método | Ruta | Quién |
|---|---|---|
| GET | `/health` (sin prefijo) | público |
| GET/POST | `/tipos-pqrs` | autenticado / administrador |
| PUT/DELETE | `/tipos-pqrs/{id}` | administrador |
| PATCH | `/tipos-pqrs/{id}/estado` | administrador |
| POST/GET | `/pqrs` | autenticado (cada uno ve las suyas; el admin todas) |
| GET | `/pqrs/{id}` | dueño o administrador |
| PATCH | `/pqrs/{id}/responder` | administrador |
| DELETE | `/pqrs/{id}` | administrador |
| GET/POST | `/comunicados` | autenticado (por rol) / administrador |
| PUT/DELETE | `/comunicados/{id}` | administrador |
| PATCH | `/comunicados/{id}/estado` | administrador |
| POST | `/valoraciones` | colegio |
| GET | `/valoraciones/evento/{id}` | autenticado |
| DELETE | `/valoraciones/{id}` | dueño o administrador |

## Usarla con el token de la API principal

1. `POST {API_PRINCIPAL}/api/v1/auth/login` → copiar `access_token`.
2. En `/docs` de esta API → **Authorize** → pegar el token.

Comprobado de punta a punta con el backend nuevo: el token del login de la API principal crea y lista PQRS aquí
(la PQRS queda con el `id_usuario` del token); un token manipulado, vencido o firmado con otra clave responde **401**.

## Seguridad: limitaciones conocidas

- **Token de un usuario eliminado o desactivado.** Esta API solo verifica la **firma y la expiración** del JWT; no consulta la
  base principal (PostgreSQL). Si el administrador elimina o desactiva a un usuario, la API principal le cierra la sesión de
  inmediato, pero **aquí su token sigue sirviendo hasta que vence** (60 minutos, `ACCESS_TOKEN_EXPIRE_MINUTES` de la API
  principal). Lo mismo pasa si le cambian el rol: el rol del token es el que tenía al iniciar sesión. Para reducir esa ventana,
  bajar `ACCESS_TOKEN_EXPIRE_MINUTES` en la API principal.
- **CORS en producción.** Si `CORS_ORIGINS` no está definida, la API acepta peticiones de **cualquier origen** (`*`). En
  producción (Render) es **obligatorio** configurarla con la URL exacta del frontend, por ejemplo
  `CORS_ORIGINS=https://conexion-escolar.onrender.com` (varias URL separadas por coma, sin `/` al final).
- **`SECRET_KEY`.** Sin ella (o con el valor de ejemplo `cambia-esto`) el servidor no arranca: debe ser la misma de la API principal.

## Despliegue (Render + MySQL en la nube)

1. MySQL gratuito: **Aiven for MySQL** (`DB_SSL=insecure`) o **TiDB Cloud Serverless** (`DB_SSL=true`). Crea la base y ejecuta `npm run init-db` (o pega `schema.sql`).
2. Render → **New Web Service** → este repositorio → **Root Directory: `aux_api`** · Build `npm install` · Start `npm start`.
3. Variables: `DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME DB_SSL`, `SECRET_KEY` (igual a la API principal) y **`CORS_ORIGINS` con la URL del frontend** (si falta, se acepta cualquier origen).
4. Probar: `https://<servicio>.onrender.com/health` debe responder `{"status":"ok","mysql":"conectado"}`.

## Pruebas

`npm test` (necesita un MySQL con la base creada y las variables `DB_*`). **Nunca contra la base de producción (Aiven):**
las pruebas crean y eliminan registros. Con un MySQL local desechable en Docker (PowerShell, desde `aux_api/`):

```
docker run -d --rm --name aux-mysql-prueba -p 127.0.0.1:3307:3306 -e MYSQL_ALLOW_EMPTY_PASSWORD=yes mysql:8.4
docker exec aux-mysql-prueba mysql -uroot -e "CREATE DATABASE conexion_escolar_aux CHARACTER SET utf8mb4"
$env:DB_HOST="127.0.0.1"; $env:DB_PORT="3307"; $env:DB_USER="root"; $env:DB_PASSWORD=""; $env:DB_SSL="false"
$env:DB_NAME="conexion_escolar_aux"; $env:SECRET_KEY="clave-solo-pruebas"
npm run init-db
npm test
docker stop aux-mysql-prueba     # se borra solo (--rm)
```

`init-db` crea las tablas pero no la base: en la nube la base ya viene creada; en local se crea con el `CREATE DATABASE` de arriba.
