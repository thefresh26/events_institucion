import os
import tempfile

# Base de datos de prueba SQLite: estos tests NO tocan Neon.
_f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ.update(DATABASE_URL=f"sqlite:///{_f.name}", SECRET_KEY="test-secret", COOKIE_SECURE="false")

from fastapi.testclient import TestClient  # noqa: E402

from app.db.session import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Ciudad, Departamento, Modulo, ModuloPorRol, Rol, Usuario  # noqa: E402

Base.metadata.create_all(engine)
with SessionLocal() as db:
    db.add_all([Rol(id=1, nombre="administrador"), Rol(id=2, nombre="organizador"), Rol(id=3, nombre="colegio")])
    db.add(Departamento(id=1, nombre="Cundinamarca"))
    db.flush()
    db.add(Ciudad(id=1, id_departamento=1, nombre="Bogota"))
    db.add(Modulo(id=1, nombre="panel"))
    db.flush()
    db.add(ModuloPorRol(id_rol=3, id_modulo=1))
    db.commit()

c = TestClient(app)
COL = dict(correo="rector@sanjose.edu.co", contrasena="Clave1234", nombre="Ana", apellido="Ruiz", nit="900123456-1",
           colegio_nombre="Colegio San Jose", id_ciudad=1)


def test_flujo_completo():
    assert c.post("/api/v1/auth/registro/colegio", json=COL).status_code == 201
    # pendiente de aprobacion: no puede entrar
    assert c.post("/api/v1/auth/login", json={"correo": COL["correo"], "contrasena": COL["contrasena"]}).status_code == 403
    assert c.get("/api/v1/auth/me").status_code == 401
    with SessionLocal() as db:  # el administrador aprueba
        db.query(Usuario).filter_by(correo=COL["correo"]).one().activo = True
        db.commit()
    r = c.post("/api/v1/auth/login", json={"correo": COL["correo"], "contrasena": COL["contrasena"]})
    assert r.status_code == 200 and r.json()["rol"] == "colegio" and r.json()["modulos"] == ["panel"]
    assert "httponly" in r.headers["set-cookie"].lower()
    assert c.get("/api/v1/auth/me").json()["id_colegio"] is not None
    assert "default-src" in r.headers["content-security-policy"]


def test_validaciones_y_seguridad():
    malo = {**COL, "correo": "otro@x.co", "nit": "1"}
    assert c.post("/api/v1/auth/registro/colegio", json=malo).status_code == 422  # NIT invalido
    assert c.post("/api/v1/auth/registro/colegio", json={**COL, "correo": "a@x.co", "nit": "800111222", "contrasena": "sololetras"}).status_code == 422
    # el cliente NO puede escoger su rol ni activarse solo
    assert c.post("/api/v1/auth/registro/colegio", json={**COL, "correo": "b@x.co", "nit": "800111333", "id_rol": 1, "activo": True}).status_code == 422
    assert c.post("/api/v1/auth/registro/colegio", json=COL).status_code == 409  # duplicado


def test_bloqueo_por_intentos():
    for _ in range(5):
        assert c.post("/api/v1/auth/login", json={"correo": "nadie@x.co", "contrasena": "mala"}).status_code == 401
    assert c.post("/api/v1/auth/login", json={"correo": "nadie@x.co", "contrasena": "mala"}).status_code == 429
