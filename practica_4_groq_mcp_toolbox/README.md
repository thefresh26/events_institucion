# Práctica 4 · Open WebUI + Groq + MCP Toolbox + mcpo

**Qué se hizo:** Open WebUI usa un modelo en la nube (Groq) y consulta una base PostgreSQL a través de **MCP Toolbox** (herramientas SQL definidas en `tools.yaml`), expuesto a Open WebUI con **mcpo** como servidor OpenAPI.

| Archivo | Para qué |
|---|---|
| `comandos.ps1` | Preparación y las dos ventanas de PowerShell (Toolbox y mcpo) |
| `tools.yaml` | Conexión a PostgreSQL y herramientas SQL (`contar_clientes`, `clientes_por_ciudad`) |
| `.env.example` | Dónde va la llave de Groq (`GROQ_API_KEY`) |

**Cómo se levanta** (detalle en `comandos.ps1`):

1. Copiar `tools.yaml` a `C:\asistente-bd` (fuera del repositorio) y poner ahí la base, el usuario y la contraseña reales.
2. Ventana 1: `.\toolbox.exe --config tools.yaml` (puerto 5000).
3. Ventana 2: `mcpo --port 8000 --api-key "<tu-clave-mcpo>" --server-type "streamable-http" -- http://127.0.0.1:5000/mcp`.
4. Open WebUI → Integraciones → Servidor de herramientas OpenAPI: `http://host.docker.internal:8000` con la misma clave.

Las llaves reales (Groq, mcpo y la contraseña de la base) **nunca** se suben al repositorio.
