import os
import tempfile

# Base de datos de prueba SQLite: estos tests NO tocan Neon.
_f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ.update(DATABASE_URL=f"sqlite:///{_f.name}", SECRET_KEY="test-secret", COOKIE_SECURE="false")

from fastapi.testclient import TestClient  # noqa: E402

from app.db.session import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import (CategoriaEvento, Ciudad, Departamento, EstadoEvento, EstadoInscripcion, Grado, Modulo,  # noqa: E402
                        ModuloPorRol, Rol, Usuario)

Base.metadata.create_all(engine)
with SessionLocal() as db:
    db.add_all([Rol(id=1, nombre="administrador"), Rol(id=2, nombre="organizador"), Rol(id=3, nombre="colegio"),
                Departamento(id=1, nombre="Cundinamarca"), Grado(id=1, nombre="9"), Modulo(id=1, nombre="panel"), CategoriaEvento(id=1, nombre="Ciencia"),
                *[EstadoEvento(nombre=n) for n in ("borrador", "pendiente", "publicado", "rechazado", "cerrado")],
                *[EstadoInscripcion(nombre=n) for n in ("pendiente", "aceptada", "rechazada")],
                Usuario(id=1, id_rol=1, correo="admin@x.co", contrasena=hash_password("Admin1234"), nombre="Ad", apellido="Min")])
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


# ---------------- Eventos, inscripciones, asistencia y reportes ----------------
from datetime import datetime, timedelta, timezone  # noqa: E402

from app.api.v1.comun import csv_seguro  # noqa: E402


def evento_json(**extra):
    base = dict(nombre="Feria de Ciencias", lugar="Coliseo", fecha_inicio=(datetime.now(timezone.utc) + timedelta(days=20)).isoformat(),
                id_categoria=1, id_ciudad=1, cupo_colegios=2, cupo_estudiantes=2)
    return {**base, **extra}


def admin():
    c = TestClient(app)
    assert c.post(f"{API}/auth/login", json={"correo": "admin@x.co", "contrasena": "Admin1234"}).status_code == 200
    return c


def publicar(org, adm, **extra):
    r = org.post(f"{API}/organizador/eventos", json=evento_json(**extra))
    assert r.status_code == 201 and r.json()["estado"] == "borrador"
    eid = r.json()["id"]
    assert org.post(f"{API}/organizador/eventos/{eid}/enviar").json()["estado"] == "pendiente"
    assert adm.patch(f"{API}/admin/eventos/{eid}/decision", json={"decision": "publicado"}).json()["estado"] == "publicado"
    return eid


def estudiante(col, doc):
    r = col.post(f"{API}/colegio/estudiantes", json={**EST, "documento": doc})
    assert r.status_code == 201
    return r.json()["id"]


def test_flujo_de_evento_completo():
    org, adm = organizador("org10@x.co", "810000001"), admin()
    col, _ = colegio_de(org, "rector10@x.co", "910000001")
    e1, e2 = estudiante(col, "1000000001"), estudiante(col, "1000000002")
    r = org.post(f"{API}/organizador/eventos", json=evento_json())
    eid = r.json()["id"]
    assert col.get(f"{API}/colegio/eventos").json() == []                                  # borrador: el colegio no lo ve
    assert col.post(f"{API}/colegio/eventos/{eid}/inscripcion", json={"estudiantes": [e1]}).status_code == 404
    assert col.post(f"{API}/organizador/eventos", json=evento_json()).status_code == 403   # un colegio no crea eventos
    assert col.patch(f"{API}/admin/eventos/{eid}/decision", json={"decision": "publicado"}).status_code == 403
    assert adm.patch(f"{API}/admin/eventos/{eid}/decision", json={"decision": "publicado"}).status_code == 409  # aun no esta pendiente
    org.post(f"{API}/organizador/eventos/{eid}/enviar")
    adm.patch(f"{API}/admin/eventos/{eid}/decision", json={"decision": "publicado"})
    assert col.get(f"{API}/colegio/eventos").json()[0]["id"] == eid
    # inscripcion
    assert col.post(f"{API}/colegio/eventos/{eid}/inscripcion", json={"estudiantes": [e1, e1]}).status_code == 422
    assert col.post(f"{API}/colegio/eventos/{eid}/inscripcion", json={"estudiantes": [e1, e2, 999]}).status_code == 422
    assert col.post(f"{API}/colegio/eventos/{eid}/inscripcion", json={"estudiantes": [e1, e2]}).status_code == 201
    assert col.post(f"{API}/colegio/eventos/{eid}/inscripcion", json={"estudiantes": [e1]}).status_code == 409  # ya inscrito
    iid = org.get(f"{API}/organizador/inscripciones").json()[0]["id"]
    assert org.patch(f"{API}/organizador/inscripciones/{iid}", json={"estado": "aceptada"}).status_code == 200
    assert org.patch(f"{API}/organizador/inscripciones/{iid}", json={"estado": "rechazada"}).status_code == 409  # ya decidida
    # asistencia
    grupo = org.get(f"{API}/organizador/eventos/{eid}/asistencia").json()[0]["estudiantes"]
    marca = [{"id_inscripcion_estudiante": grupo[0]["id_inscripcion_estudiante"], "asistio": True}]
    assert org.put(f"{API}/organizador/eventos/{eid}/asistencia", json={"marcas": marca}).status_code == 204
    assert org.put(f"{API}/organizador/eventos/{eid}/asistencia", json={"marcas": [{"id_inscripcion_estudiante": 9999, "asistio": True}]}).status_code == 422
    # reportes
    rep = org.get(f"{API}/organizador/eventos/{eid}/reporte/estudiantes.csv")
    assert rep.status_code == 200 and "text/csv" in rep.headers["content-type"] and "Si" in rep.text and "1000000001" not in rep.text
    assert "Colegio 910000001" in org.get(f"{API}/organizador/eventos/{eid}/reporte/colegios.csv").text


def test_cupos_y_aislamiento_de_eventos():
    org1, org2, adm = organizador("org11@x.co", "810000002"), organizador("org12@x.co", "810000003"), admin()
    colA, _ = colegio_de(org1, "rector11@x.co", "910000002")
    colB, _ = colegio_de(org2, "rector12@x.co", "910000003")
    eid = publicar(org1, adm, cupo_colegios=1, cupo_estudiantes=1)
    a1, a2 = estudiante(colA, "2000000001"), estudiante(colA, "2000000002")
    b1 = estudiante(colB, "2000000003")
    assert colB.get(f"{API}/colegio/eventos").json() == []                                         # evento de otro organizador
    assert colB.post(f"{API}/colegio/eventos/{eid}/inscripcion", json={"estudiantes": [b1]}).status_code == 404
    assert colA.post(f"{API}/colegio/eventos/{eid}/inscripcion", json={"estudiantes": [a1, a2]}).status_code == 422  # cupo por colegio
    assert colA.post(f"{API}/colegio/eventos/{eid}/inscripcion", json={"estudiantes": [b1]}).status_code == 422      # estudiante ajeno
    assert colA.post(f"{API}/colegio/eventos/{eid}/inscripcion", json={"estudiantes": [a1]}).status_code == 201
    assert org2.put(f"{API}/organizador/eventos/{eid}", json=evento_json()).status_code == 404       # evento de otro organizador
    assert org2.post(f"{API}/organizador/eventos/{eid}/enviar").status_code == 404
    assert org2.get(f"{API}/organizador/eventos/{eid}/reporte/estudiantes.csv").status_code == 404
    assert org1.put(f"{API}/organizador/eventos/{eid}", json=evento_json()).status_code == 409       # publicado: ya no se edita
    assert org1.post(f"{API}/organizador/eventos", json=evento_json(cupo_colegios=0)).status_code == 422
    assert org1.post(f"{API}/organizador/eventos", json=evento_json(fecha_fin="2000-01-01T00:00:00Z")).status_code == 422


def test_csv_no_ejecuta_formulas():
    assert csv_seguro("=HYPERLINK(\"http://malo\")") == "'=HYPERLINK(\"http://malo\")"
    assert csv_seguro("Ana") == "Ana" and csv_seguro(None) == ""


def test_frontend_servido_con_cabeceras_de_seguridad():
    from pathlib import Path
    if not (Path(__file__).resolve().parents[1] / "app" / "frontend_dist" / "index.html").is_file():
        return  # el frontend aun no esta compilado
    c = TestClient(app)
    for ruta in ("/", "/login", "/panel", "/admin/eventos"):  # rutas reales de la SPA
        r = c.get(ruta)
        assert r.status_code == 200 and "<html" in r.text
        assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
        assert r.headers["x-content-type-options"] == "nosniff"
    assert c.get("/robots.txt").status_code == 200
    assert c.get("/../.env").status_code in (200, 404) and "SECRET_KEY" not in c.get("/../.env").text  # no se sale de la carpeta
    # 404 real para rutas inventadas, y el cache correcto en cada tipo de recurso
    assert c.get("/ruta-inventada").status_code == 404 and c.get("/docs").status_code == 404
    assert c.get("/api/v1/no-existe").status_code == 404
    assert c.get("/api/v1/catalogos/grados").headers["cache-control"] == "no-store"
    assert c.get("/login").headers["cache-control"] == "no-cache"
    assert "gzip" in c.get("/login", headers={"accept-encoding": "gzip"}).headers.get("content-encoding", "gzip")


# ---------------- Administracion de usuarios y roles ----------------
def test_admin_gestiona_usuarios_y_roles():
    from app.db.seed import asegurar_modulos_admin
    with SessionLocal() as db:
        asegurar_modulos_admin(db)
        asegurar_modulos_admin(db)  # idempotente
    adm = admin()
    assert {"usuarios", "roles"} <= set(adm.get(f"{API}/auth/me").json()["modulos"])
    # un organizador no entra a estas rutas
    org = organizador("org20@x.co", "820000001")
    assert org.get(f"{API}/admin/usuarios").status_code == 403 and org.get(f"{API}/admin/roles").status_code == 403
    # el admin crea un organizador activo con contrasena temporal y ese organizador puede entrar
    r = adm.post(f"{API}/admin/usuarios", json=dict(correo="Nuevo.Org@x.co", nombre="Luis", apellido="Paz", rol="organizador",
                                                    organizacion_nombre="Fundacion Nueva", nit="820000002"))
    assert r.status_code == 201 and r.json()["usuario"]["perfil"] == "Fundacion Nueva"
    c = TestClient(app)
    assert c.post(f"{API}/auth/login", json={"correo": "nuevo.org@x.co", "contrasena": r.json()["contrasena_temporal"]}).status_code == 200
    assert c.get(f"{API}/organizador/eventos").status_code == 200
    # validaciones
    assert adm.post(f"{API}/admin/usuarios", json=dict(correo="a1@x.co", nombre="Ana", apellido="Paz", rol="organizador")).status_code == 422
    assert adm.post(f"{API}/admin/usuarios", json=dict(correo="a2@x.co", nombre="Ana", apellido="Paz", rol="colegio")).status_code == 422
    assert adm.post(f"{API}/admin/usuarios", json=dict(correo="nuevo.org@x.co", nombre="Ana", apellido="Paz", rol="administrador")).status_code == 409
    # crear otro administrador, cambiar datos, desactivar y restablecer
    a2 = adm.post(f"{API}/admin/usuarios", json=dict(correo="adm2@x.co", nombre="Eva", apellido="Sol", rol="administrador")).json()
    uid = a2["usuario"]["id"]
    assert adm.patch(f"{API}/admin/usuarios/{uid}", json={"nombre": "Evelyn"}).json()["nombre"] == "Evelyn"
    assert adm.patch(f"{API}/admin/usuarios/{uid}", json={"rol": "organizador"}).status_code == 409   # sin perfil de organizador
    assert adm.patch(f"{API}/admin/usuarios/{uid}", json={"id_rol": 3}).status_code == 422            # campos no permitidos
    assert adm.patch(f"{API}/admin/usuarios/{uid}", json={"activo": False}).json()["activo"] is False
    assert adm.post(f"{API}/admin/usuarios/{uid}/restablecer").json()["contrasena_temporal"]
    # un organizador puede volverse administrador (y volver, porque conserva su perfil)
    oid = adm.get(f"{API}/admin/usuarios", params={"q": "org20"}).json()[0]["id"]
    assert adm.patch(f"{API}/admin/usuarios/{oid}", json={"rol": "administrador"}).json()["rol"] == "administrador"
    assert adm.patch(f"{API}/admin/usuarios/{oid}", json={"rol": "organizador"}).json()["rol"] == "organizador"
    # el admin no se puede quitar el acceso a si mismo
    yo = adm.get(f"{API}/admin/usuarios", params={"q": "admin@x.co"}).json()[0]["id"]
    assert adm.patch(f"{API}/admin/usuarios/{yo}", json={"activo": False}).status_code == 409
    assert adm.patch(f"{API}/admin/usuarios/{yo}", json={"rol": "colegio"}).status_code == 409
    assert adm.post(f"{API}/admin/usuarios/{yo}/restablecer").status_code == 409
    assert adm.patch(f"{API}/admin/usuarios/99999", json={"nombre": "Xx"}).status_code == 404
    assert adm.get(f"{API}/admin/usuarios", params={"rol": "administrador", "estado": "activo"}).status_code == 200
    # roles y modulos
    d = adm.get(f"{API}/admin/roles").json()
    por = {r["nombre"]: r for r in d["roles"]}
    assert por["administrador"]["bloqueado"] and por["organizador"]["usuarios"] >= 1
    panel = next(m["id"] for m in d["modulos"] if m["nombre"] == "panel")
    assert adm.put(f"{API}/admin/roles/{por['organizador']['id']}/modulos", json={"modulos": [panel]}).json()["modulos"] == [panel]
    assert adm.put(f"{API}/admin/roles/{por['organizador']['id']}/modulos", json={"modulos": [99999]}).status_code == 422
    assert adm.put(f"{API}/admin/roles/{por['administrador']['id']}/modulos", json={"modulos": []}).status_code == 409
    assert org.put(f"{API}/admin/roles/1/modulos", json={"modulos": []}).status_code == 403
