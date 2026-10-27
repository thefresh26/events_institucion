# Práctica 4 - Open WebUI + Groq + MCP Toolbox + mcpo
# Se usan DOS ventanas de PowerShell abiertas al mismo tiempo (no cerrarlas mientras se use).
# Carpeta de trabajo: C:\asistente-bd (fuera del repositorio: contiene toolbox.exe y la contraseña en tools.yaml)

# ---------- PREPARACIÓN (una sola vez) ----------
# 1. Descargar toolbox.exe (windows/amd64) de https://github.com/googleapis/mcp-toolbox/releases a C:\asistente-bd
# 2. Copiar tools.yaml de esta carpeta a C:\asistente-bd y editar database / user / password.
#    Nota: con Toolbox 1.15.0 el archivo usa "kind: source" y "kind: tool" (singular).
# 3. Instalar mcpo con versiones compatibles:
#    pip install mcpo
#    pip install "mcp>=1.17,<2"
#    pip install "fastapi==0.115.12"

# ---------- VENTANA 1: Toolbox (puerto 5000) ----------
cd C:\asistente-bd
# Quitar la marca BOM si el archivo se guardó con el Bloc de notas:
$t = [IO.File]::ReadAllText("C:\asistente-bd\tools.yaml"); [IO.File]::WriteAllText("C:\asistente-bd\tools.yaml", $t.TrimStart([char]0xFEFF), (New-Object Text.UTF8Encoding($false)))
.\toolbox.exe --config tools.yaml

# ---------- VENTANA 2: mcpo (puerto 8000) ----------
# (cerrar antes uvicorn de api2026, que usa el mismo puerto 8000)
cd C:\asistente-bd
mcpo --port 8000 --api-key "<tu-clave-mcpo>" --server-type "streamable-http" -- http://127.0.0.1:5000/mcp

# ---------- OPEN WEBUI ----------
# Configuración de administrador > Integraciones > Servidores de Herramientas Externos > +
#   Tipo OpenAPI | URL http://host.docker.internal:8000 | Bearer: la misma <tu-clave-mcpo>
