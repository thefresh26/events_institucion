"""Crea el primer administrador. Uso (desde la carpeta backend/, con el .env listo):
    python -m scripts.crear_admin
La contrasena se pide por teclado (no queda en el historial ni en el chat)."""
import getpass

from app.core.security import hash_password
from app.core.database import Database

correo = input("Correo del administrador: ").strip().lower()
nombre = input("Nombre: ").strip()
apellido = input("Apellido: ").strip()
clave = getpass.getpass("Contrasena (min 8, letras y numeros): ")
if len(clave) < 8 or len(clave) > 72 or clave.isalpha() or clave.isdigit():
    raise SystemExit("Contrasena muy debil")

with Database().get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM usuario WHERE correo = %s;", (correo,))
    if cursor.fetchone():
        raise SystemExit("Ese correo ya existe")
    cursor.execute("""
        INSERT INTO usuario (id_rol, correo, contrasena, nombre, apellido, activo)
        VALUES ((SELECT id FROM rol WHERE nombre = 'administrador'), %s, %s, %s, %s, true);
    """, (correo, hash_password(clave), nombre, apellido))
print("Administrador creado.")
