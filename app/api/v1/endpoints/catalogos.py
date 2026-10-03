from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import CategoriaEvento, Ciudad, Grado

router = APIRouter(prefix="/catalogos", tags=["catalogos"])


@router.get("/ciudades")
def ciudades(db: Session = Depends(get_db)):
    return [{"id": c.id, "nombre": c.nombre, "departamento": c.departamento.nombre}
            for c in db.query(Ciudad).order_by(Ciudad.nombre).limit(2000)]


@router.get("/grados")
def grados(db: Session = Depends(get_db)):
    return [{"id": g.id, "nombre": g.nombre} for g in db.query(Grado).order_by(Grado.id)]


@router.get("/categorias")
def categorias(db: Session = Depends(get_db)):
    return [{"id": c.id, "nombre": c.nombre} for c in db.query(CategoriaEvento).order_by(CategoriaEvento.nombre)]
