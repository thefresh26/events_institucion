# PRÁCTICA 3 - Open WebUI con Ollama y PostgreSQL (Python 3.11 o 3.12)
# Ejecutar estos comandos desde esta carpeta (ia/text_to_sql).

# 1) Ollama (https://ollama.com/) ya instalado
ollama --version
ollama pull qwen3:1.7b
ollama pull qwen2.5:1.5b-instruct
ollama list

# 2) Entorno virtual (en las capturas del profesor se llama myvenv)
python -m venv myvenv
.\myvenv\Scripts\Activate.ps1
python --version

# 3) Instalar
pip install psycopg2-binary
pip install open-webui      # puede demorar

# 4) Correr el servidor (http://localhost:8080)
open-webui serve

# 5) En Open WebUI (según las capturas):
#    - Crear la cuenta de administrador.
#    - Espacio de Trabajo -> Herramientas -> Nueva Herramienta:
#      pegar el contenido de postgresql_text_to_sql.py y Guardar.
#    - Engranaje de la herramienta (Válvulas): host de Neon, puerto 5432,
#      base neondb, usuario ia_lectura y su contraseña (creado con ia/ia_lectura.sql).
#    - Espacio de Trabajo -> Modelos -> editar el modelo: pegar
#      prompt_del_sistema.txt y activar la herramienta postgres_tool.
#    - Nuevo chat con ese modelo y preguntar, por ejemplo: ¿cuántos colegios están inscritos en cada evento?
