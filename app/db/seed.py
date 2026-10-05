"""Datos minimos que el codigo necesita (idempotente: se puede ejecutar en cada arranque)."""
from sqlalchemy.orm import Session

from app.models import Modulo, ModuloPorRol, Rol

# Modulos nuevos del panel de administracion; se asignan al rol administrador.
MODULOS_ADMIN = {"usuarios": "Gestión de usuarios", "roles": "Roles y módulos"}


def asegurar_modulos_admin(db: Session) -> None:
    rol = db.query(Rol).filter_by(nombre="administrador").first()
    if rol is None:
        return
    for nombre, descripcion in MODULOS_ADMIN.items():
        m = db.query(Modulo).filter_by(nombre=nombre).first() or Modulo(nombre=nombre, descripcion=descripcion)
        db.add(m)
        db.flush()
        if not db.query(ModuloPorRol).filter_by(id_rol=rol.id, id_modulo=m.id).first():
            db.add(ModuloPorRol(id_rol=rol.id, id_modulo=m.id))
    db.commit()
