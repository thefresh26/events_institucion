# Práctica 3 · Open WebUI + Ollama + PostgreSQL (text-to-SQL)

**Qué se hizo:** Open WebUI instalado con `pip` y una herramienta que le permite al modelo consultar una base PostgreSQL local (solo `SELECT`), respondiendo preguntas en español con los datos reales.

| Archivo | Para qué |
|---|---|
| `comandos.ps1` | Instalación y arranque paso a paso |
| `postgresql_text_to_sql.py` | Herramienta para Open WebUI (`get_schema` y `run_sql_query`, solo lectura) |
| `prompt_del_sistema.txt` | Prompt del modelo: siempre usar la herramienta, nunca mostrar el SQL |

**Cómo se levanta:**

```powershell
python -m venv myvenv
.\myvenv\Scripts\Activate.ps1
pip install psycopg2-binary open-webui
open-webui serve          # http://localhost:8080
```

En Open WebUI: Espacio de trabajo → Herramientas → pegar `postgresql_text_to_sql.py`. La **contraseña de PostgreSQL se escribe en las Válvulas** de la herramienta; en este archivo va vacía a propósito.
