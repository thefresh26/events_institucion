"""Puente hacia la API auxiliar (Express + MySQL).

El navegador solo habla con esta API (misma URL y misma cookie de sesion). Aqui se toma el JWT de la cookie
y se reenvia a Express como "Authorization: Bearer", asi el frontend nunca maneja el token."""
import httpx
from fastapi import APIRouter, HTTPException, Request, Response

from app.core.config import settings

router = APIRouter(prefix="/aux", tags=["API auxiliar (PQRS, comunicados y valoraciones)"])


@router.api_route("/{ruta:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def reenviar(ruta: str, request: Request):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="No se pudo validar la sesión")
    if ".." in ruta or ruta.startswith("/"):
        raise HTTPException(status_code=400, detail="Ruta inválida")
    cuerpo = await request.body()
    cabeceras = {"Authorization": f"Bearer {token}"}
    if cuerpo:
        cabeceras["Content-Type"] = "application/json"
    try:
        async with httpx.AsyncClient(timeout=60) as cliente:  # 60 s: el plan gratis de Render tarda en despertar
            r = await cliente.request(request.method, f"{settings.aux_api_url}/api/aux/{ruta}",
                                      content=cuerpo or None, headers=cabeceras)
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="La API auxiliar no responde. Intenta de nuevo en un momento.")
    return Response(content=r.content, status_code=r.status_code, media_type=r.headers.get("content-type", "application/json"))
