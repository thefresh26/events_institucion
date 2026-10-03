import os
import tempfile

# Base de datos de prueba SQLite: estos tests NO tocan Neon.
_f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ.update(DATABASE_URL=f"sqlite:///{_f.name}", SECRET_KEY="test-secret", COOKIE_SECURE="false")

from fastapi.testclient import TestClient  # noqa: E402

from app.db.session import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Ciudad, Departamento, Grado, Modulo, ModuloPorRol, Rol, Usuario  # noqa: E402

Base.metadata.create_all(engine)
with SessionLocal() as db:
    db.add_all([Rol(id=1, nombre="administrador"), Rol(id=2, nombre="organizador"), Rol(id=3, nombre="colegio"),
                Departamento(id=1, nombre="Cundinamarca"), Grado(id=1, nombre="9"), Modulo(id=1, nombre="panel")])
    db.flush()
    db.add_all([Ciudad(id=1, id_departamento=1, nombre="Bogota"), ModuloPorRol(id_rol=3, id_modulo=1)])
    db.commit()

API = "/api/v1"


def aprobar(correo):
    with SessionLocal() as db:
        db.query(Usuario).filter_by(correo=correo).one().activo = True
        db.commit()


def organizador(correo, nit):
    c = TestClient(app)
    r = c.post(f"{API}/auth/registro/organizador", json=dict(correo=correo, contrasena="Clave1234", nombre="Org", apellido="Uno",
                                                              nit=nit, organizacion_nombre="Fundacion " + nit))
    assert r.status_code == 201
    assert c.post(f"{API}/auth/login", json={"correo": correo, "contrasena": "Clave1234"}).status_code == 403  # pendiente
    aprobar(correo)
    r = c.post(f"{API}/auth/login", json={"correo": correo, "contrasena": "Clave1234"})
    assert r.status_code == 200 and "httponly" in r.headers["set-cookie"].lower()
    assert "default-src" in r.headers["content-security-policy"]
    return c


def colegio_de(org, correo, nit):
    r = org.post(f"{API}/organizador/colegios", json=dict(correo=correo, nombre="Ana", apellido="Ruiz", nit=nit,
                                                          colegio_nombre="Colegio " + nit, id_ciudad=1))
    assert r.status_code == 201
    c = TestClient(app)
    assert c.post(f"{API}/auth/login", json={"correo": correo, "contrasena": r.json()["contrasena_temporal"]}).status_code == 200
    return c, r.json()["colegio"]["id"]


EST = dict(nombre="Valentina", apellido="Rios", documento="1098765421", id_grado=1, nombre_acudiente="Maria Rios", acudiente_autoriza=True)


def test_flujo_organizador_colegio_estudiante():
    org = organizador("org1@x.co", "800000001")
    col, id_col = colegio_de(org, "rector1@x.co", "900000001")
    assert col.get(f"{API}/auth/me").json()["modulos"] == ["panel"]
    r = col.post(f"{API}/colegio/estudiantes", json=EST)
    assert r.status_code == 201 and r.json()["documento"] == "109*****21"  # enmascarado
    assert col.post(f"{API}/colegio/estudiantes", json=EST).status_code == 409  # duplicado
    assert len(col.get(f"{API}/colegio/estudiantes").json()) == 1
    # contrasena temporal -> cambia por una propia
    assert col.post(f"{API}/auth/cambiar-contrasena", json={"actual": "mala", "nueva": "Nueva1234"}).status_code == 400


def test_aislamiento_entre_actores():
    org1, org2 = organizador("org2@x.co", "800000002"), organizador("org3@x.co", "800000003")
    col1, id1 = colegio_de(org1, "rector2@x.co", "900000002")
    col2, _ = colegio_de(org2, "rector3@x.co", "900000003")
    e = col1.post(f"{API}/colegio/estudiantes", json=EST).json()
    assert col2.get(f"{API}/colegio/estudiantes").json() == []                       # no ve estudiantes ajenos
    assert col2.delete(f"{API}/colegio/estudiantes/{e['id']}").status_code == 404    # IDOR bloqueado
    assert org2.patch(f"{API}/organizador/colegios/{id1}/activo", json={"activo": False}).status_code == 404
    assert org2.get(f"{API}/organizador/colegios").json()[0]["nit"] == "900000003"   # solo los suyos
    assert col1.get(f"{API}/organizador/colegios").status_code == 403                # un colegio no es organizador
    assert TestClient(app).get(f"{API}/colegio/estudiantes").status_code == 401      # sin sesion


def test_validaciones():
    c = TestClient(app)
    base = dict(correo="z@x.co", contrasena="Clave1234", nombre="Org", apellido="Uno", nit="800000009", organizacion_nombre="Fundacion Z")
    assert c.post(f"{API}/auth/registro/organizador", json={**base, "nit": "1"}).status_code == 422
    assert c.post(f"{API}/auth/registro/organizador", json={**base, "contrasena": "sololetras"}).status_code == 422
    assert c.post(f"{API}/auth/registro/organizador", json={**base, "id_rol": 1, "activo": True}).status_code == 422  # no elige su rol
    assert c.post(f"{API}/auth/registro/colegio", json=base).status_code in (404, 405)  # el colegio ya no se registra solo


def test_bloqueo_por_intentos():
    c = TestClient(app)
    for _ in range(5):
        assert c.post(f"{API}/auth/login", json={"correo": "nadie@x.co", "contrasena": "mala"}).status_code == 401
    assert c.post(f"{API}/auth/login", json={"correo": "nadie@x.co", "contrasena": "mala"}).status_code == 429
