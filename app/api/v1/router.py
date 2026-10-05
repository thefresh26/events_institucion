from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, catalogos, colegio, organizador, usuarios

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(usuarios.router)
api_router.include_router(catalogos.router)
api_router.include_router(organizador.router)
api_router.include_router(colegio.router)
