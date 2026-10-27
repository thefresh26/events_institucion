# PRÁCTICA 1 - Open WebUI con Docker + Ollama
# Requisitos: Docker Desktop y Ollama instalados.
ollama --version
ollama pull qwen3:1.7b
ollama pull qwen2.5:1.5b-instruct
# Modelo que usa el profesor en las capturas (2.5 GB)
ollama pull qwen3:4b-thinking-2507-q4_K_M
ollama list

# Comando del profesor (Open WebUI en http://localhost:3000/)
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main
