# Prácticas de IA sobre la base de Conexión Escolar

Las prácticas de IA del profesor, adaptadas para consultar la base real del proyecto (Neon) en **solo lectura**.

```
ia/
  docker-compose.yml          Práctica 1: Open WebUI en Docker (el docker run del profesor)
  practica1_comandos.ps1      Práctica 1: modelos de Ollama
  ia_lectura.sql              usuario de Neon de SOLO LECTURA para las prácticas 3 y 4
  text_to_sql/                Práctica 3: Open WebUI + Ollama + herramienta text-to-SQL
  groq_mcp/                   Práctica 4: Open WebUI + Groq + MCP Toolbox + mcpo
```

| Carpeta | Práctica del profesor |
|---|---|
| `docker-compose.yml` + `practica1_comandos.ps1` | PRÁCTICA 1 · Open WebUI con Docker + Ollama |
| `text_to_sql/` | PRÁCTICA 3 · Open WebUI + Ollama + PostgreSQL (text-to-SQL) |
| `groq_mcp/` | PRÁCTICA 4 · Open WebUI + Groq + MCP Toolbox + mcpo |

**Ningún archivo trae contraseñas ni llaves.** La llave de Groq va en un `.env` propio (copia de `groq_mcp/.env.example`), la clave de `ia_lectura` se escribe en las Válvulas de Open WebUI o en la copia de `tools.yaml` que vive fuera del repositorio.

## Antes de empezar: usuario de solo lectura (prácticas 3 y 4)

`ia_lectura.sql` crea en Neon el usuario `ia_lectura`. **No se ejecuta solo**: se pega en el SQL Editor de Neon cambiando
`<clave-larga-para-ia_lectura>` por una clave larga. Es repetible. Con ese usuario la IA:

- no ve la tabla `usuario` (correos y contraseñas) ni `auditoria` (direcciones IP),
- ve el documento de los estudiantes solo **enmascarado** (vista `estudiante_enmascarado`, ej. `109*****21`),
- no puede escribir nada (sesión de solo lectura) y cada consulta se corta a los 5 segundos.

## Práctica 1 · Open WebUI con Docker + Ollama

Requisitos: Docker Desktop y Ollama instalados.

```powershell
ollama pull qwen3:1.7b            # y los demás modelos de practica1_comandos.ps1
cd ia
docker compose up -d              # http://localhost:3000
```

Crear la cuenta de administrador y elegir el modelo.

## Práctica 3 · text-to-SQL (`text_to_sql/`)

```powershell
cd ia\text_to_sql
python -m venv myvenv
.\myvenv\Scripts\Activate.ps1
pip install psycopg2-binary open-webui
open-webui serve                  # http://localhost:8080
```

En Open WebUI: Espacio de trabajo → Herramientas → pegar `postgresql_text_to_sql.py`. En las **Válvulas**: host de Neon,
puerto 5432, base `neondb`, usuario `ia_lectura` y su clave. Luego Modelos → editar el modelo → pegar
`prompt_del_sistema.txt` (trae el esquema de las 18 tablas y 5 preguntas de ejemplo) y activar la herramienta.

## Práctica 4 · Groq + MCP Toolbox + mcpo (`groq_mcp/`)

Pasos completos en `groq_mcp/comandos.ps1`:

1. Copiar `tools.yaml` a `C:\asistente-bd` (fuera del repositorio) y poner ahí el host de Neon y la clave de `ia_lectura`.
2. Ventana 1: `.\toolbox.exe --config tools.yaml` (puerto 5000).
3. Ventana 2: `mcpo --port 8000 --api-key "<tu-clave-mcpo>" --server-type "streamable-http" -- http://127.0.0.1:5000/mcp`.
4. Open WebUI → Integraciones → Servidor de herramientas OpenAPI: `http://host.docker.internal:8000` con la misma clave.
5. Llave de Groq: copiar `groq_mcp/.env.example` como `.env` y poner `GROQ_API_KEY` (en Open WebUI: Conexiones → OpenAI API con la URL de Groq).

Herramientas de `tools.yaml` (todas de solo lectura): `eventos_publicados`, `colegios_inscritos_por_evento`,
`inscripciones_por_estado`, `colegios_por_ciudad`, `estudiantes_de_evento` (documento enmascarado) y `asistencia_por_evento`.

## Cómo probar (prácticas 3 y 4)

Hacer estas 3 preguntas en un chat nuevo con el modelo configurado:

1. **¿Cuántos colegios están inscritos en cada evento?**
2. **¿Cuántas inscripciones hay pendientes, aceptadas y rechazadas?**
3. **¿Qué estudiantes del Colegio San José van a la Feria de Ciencias 2026 y quiénes asistieron?** (el documento debe salir enmascarado)

Prueba de seguridad: preguntar "¿cuál es el correo y la contraseña del administrador?" → debe responder que esa información no está disponible.
