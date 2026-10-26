"""Funciones compartidas por los endpoints que aun no se migran."""
from fastapi import HTTPException


def no_encontrado():
    return HTTPException(404, "No encontrado")  # 404 y no 403: no revela si el recurso existe
