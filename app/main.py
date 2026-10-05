import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings

log = logging.getLogger("events")
# docs_url=None: no exponemos la documentacion interactiva en produccion.

@asynccontextmanager
async def lifespan(_: FastAPI):
    try:  # modulos del panel de administracion (idempotente); un fallo aqui no debe tumbar el servidor
        from app.db.seed import asegurar_modulos_admin
        from app.db.session import SessionLocal
        with SessionLocal() as db:
            asegurar_modulos_admin(db)
    except Exception:
        log.exception("No se pudieron asegurar los modulos de administracion")
    yield


app = FastAPI(title="Eventos para colegios - API", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)

app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(CORSMiddleware, allow_origins=settings.origenes_permitidos, allow_credentials=True,
                   allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Content-Type"])

CABECERAS = {
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
                               "img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


@app.middleware("http")
async def seguridad(request: Request, call_next):
    if settings.forzar_https and request.headers.get("x-forwarded-proto", "https") == "http":
        return RedirectResponse(str(request.url.replace(scheme="https")), status_code=301)
    try:
        response = await call_next(request)
    except Exception:
        log.exception("Error no controlado en %s %s", request.method, request.url.path)
        response = JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})  # sin detalles internos
    response.headers.update(CABECERAS)
    ruta = request.url.path
    if ruta.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"  # datos privados: que ningun cache los guarde
    elif ruta.startswith("/_app/immutable/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"  # archivos con hash en el nombre
    elif "Cache-Control" not in response.headers:
        response.headers["Cache-Control"] = "no-cache"  # la pagina base siempre se revalida
    return response


app.include_router(api_router, prefix="/api/v1")

# Frontend compilado (SvelteKit adapter-static), cuando exista.
DIST = Path(__file__).resolve().parent / "frontend_dist"
if (DIST / "index.html").is_file():
    app.mount("/_app", StaticFiles(directory=DIST / "_app"), name="assets")

    # Rutas que existen en el frontend. Cualquier otra devuelve un 404 REAL (la pagina base
    # se entrega igual para que SvelteKit muestre su pantalla "Página no encontrada").
    RUTAS_SPA = {"", "login", "registro", "politica-de-privacidad", "terminos", "panel", "cuenta", "admin", "organizador", "colegio"}

    @app.get("/{ruta:path}", include_in_schema=False)
    def frontend(ruta: str):
        base = DIST.resolve()
        pedido = (base / ruta).resolve()
        if base in pedido.parents and pedido.is_file():
            return FileResponse(pedido)
        if ruta.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "No encontrado"})
        estado = 200 if ruta.strip("/").split("/")[0] in RUTAS_SPA else 404
        return FileResponse(base / "index.html", status_code=estado)
else:
    @app.get("/")
    def raiz():
        return {"status": "ok"}
