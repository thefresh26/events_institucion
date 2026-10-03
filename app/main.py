import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings

log = logging.getLogger("events")
# docs_url=None: no exponemos la documentacion interactiva en produccion.
app = FastAPI(title="Eventos para colegios - API", docs_url=None, redoc_url=None, openapi_url=None)

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
    return response


app.include_router(api_router, prefix="/api/v1")

# Frontend compilado (SvelteKit adapter-static), cuando exista.
DIST = Path(__file__).resolve().parent / "frontend_dist"
if (DIST / "index.html").is_file():
    app.mount("/_app", StaticFiles(directory=DIST / "_app"), name="assets")

    @app.get("/{ruta:path}", include_in_schema=False)
    def frontend(ruta: str):
        base = DIST.resolve()
        pedido = (base / ruta).resolve()
        if base in pedido.parents and pedido.is_file():
            return FileResponse(pedido)
        return FileResponse(base / "index.html")
else:
    @app.get("/")
    def raiz():
        return {"status": "ok"}
