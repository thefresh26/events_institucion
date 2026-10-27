# Práctica 1 · Open WebUI con Docker + Ollama

**Qué se hizo:** se instaló Ollama con modelos locales pequeños (qwen) y se levantó Open WebUI en un contenedor Docker que habla con Ollama del computador.

**Requisitos:** Docker Desktop y Ollama instalados.

**Cómo se levanta** (comandos completos en `comandos.ps1`):

```powershell
ollama pull qwen3:1.7b
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main
```

Abrir http://localhost:3000, crear la cuenta de administrador y elegir el modelo.
