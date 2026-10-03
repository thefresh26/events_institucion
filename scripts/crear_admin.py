"""Crea el primer administrador. Uso (desde la carpeta del proyecto, con el .env listo):
    python -m scripts.crear_admin
La contrasena se pide por teclado (no queda en el historial ni en el chat)."""
import getpass

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Rol, Usuario

correo = input("Correo del administrador: ").strip().lower()
nombre = input("Nombre: ").strip()
apellido = input("Apellido: ").strip()
clave = getpass.getpass("Contrasena (min 8, letras y numeros): ")
if len(clave) < 8 or len(clave) > 72 or clave.isalpha() or clave.isdigit():
    raise SystemExit("Contrasena muy debil")

with SessionLocal() as db:
    rol = db.query(Rol).filter_by(nombre="administrador").one()
    if db.query(Usuario).filter_by(correo=correo).first():
        raise SystemExit("Ese correo ya existe")
    db.add(Usuario(id_rol=rol.id, correo=correo, contrasena=hash_password(clave), nombre=nombre, apellido=apellido, activo=True))
    db.commit()
print("Administrador creado.")
