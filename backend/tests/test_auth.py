import os
from urllib.parse import unquote, urlparse

# Base PostgreSQL de PRUEBA (los repositorios usan SQL puro de PostgreSQL, SQLite ya no sirve).
# Se BORRA y se recrea en cada corrida: NUNCA apuntar a Neon. Ej: postgresql://postgres@localhost:5499/pruebas
assert "neon.tech" not in os.environ["TEST_DATABASE_URL"], "TEST_DATABASE_URL apunta a Neon: los tests borrarían los datos reales"
_u = urlparse(os.environ["TEST_DATABASE_URL"])  # se reparte en las 5 variables DB_* que lee app/core/database.py
os.environ.update(DB_HOST=_u.hostname, DB_PORT=str(_u.port or 5432), DB_NAME=_u.path.lstrip("/"), DB_USER=unquote(_u.username or ""),
                  DB_PASSWORD=unquote(_u.password or ""), SECRET_KEY="test-secret", COOKIE_SECURE="false")

from pathlib import Path  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from app.core.database import Database  # noqa: E402
from app.core.security import hash_password  # noqa: E402

ESQUEMA = Path(__file__).resolve().parents[1] / "scripts" / "schema.sql"


def sql(consulta, *valores):
    """Consulta directa a la base de prueba (SQL puro, como los repositorios)."""
    with Database().get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(consulta, valores)
        return cursor.fetchall() if cursor.description else None


def acciones(tabla, registro_id):
    return [f["accion"] for f in sql("SELECT accion FROM auditoria WHERE tabla = %s AND registro_id = %s ORDER BY id", tabla, registro_id)]


# Base nueva en cada corrida: se borra todo y se crea con scripts/schema.sql (el mismo esquema de Neon).
sql("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
sql(ESQUEMA.read_text(encoding="utf-8"))
sql("""
    INSERT INTO rol (id, nombre) VALUES (1, 'administrador'), (2, 'organizador'), (3, 'colegio');
    INSERT INTO departamento (id, nombre) VALUES (1, 'Cundinamarca');
    INSERT INTO ciudad (id, id_departamento, nombre) VALUES (1, 1, 'Bogota');
    INSERT INTO grado (id, nombre) VALUES (1, '9');
    INSERT INTO modulo (id, nombre) VALUES (1, 'panel');
    INSERT INTO modulo_por_rol (id_rol, id_modulo) VALUES (3, 1);
    INSERT INTO categoria_evento (id, nombre) VALUES (1, 'Ciencia');
    INSERT INTO estado_evento (nombre) VALUES ('borrador'), ('pendiente'), ('publicado'), ('rechazado'), ('cerrado');
    INSERT INTO estado_inscripcion (nombre) VALUES ('pendiente'), ('aceptada'), ('rechazada');
    INSERT INTO usuario (id, id_rol, correo, contrasena, nombre, apellido, activo) VALUES (1, 1, 'admin@x.co', %s, 'Ad', 'Min', true);
""", hash_password("Admin1234"))
for t in [f["table_name"] for f in sql("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")]:
    # los id puestos a mano no avanzan la secuencia de PostgreSQL
    sql(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), COALESCE((SELECT MAX(id) FROM {t}), 0) + 1, false)")

API = "/api/v1"


def aprobar(correo):
    sql("UPDATE usuario SET activo = true WHERE correo = %s", correo)


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
    assert org1.patch(f"{API}/organizador/colegios/{id1}/activo", json={"activo": True}).json()["activo"] is True
    hechas = acciones("colegio", id1)                                              # quedan auditadas
    assert hechas == ["registrar_colegio", "activar_colegio"]
    assert org2.get(f"{API}/organizador/colegios").json()[0]["nit"] == "900000003"   # solo los suyos
    assert col1.get(f"{API}/organizador/colegios").status_code == 403                # un colegio no es organizador
    assert TestClient(app).get(f"{API}/colegio/estudiantes").status_code == 401      # sin sesion
    assert col1.delete(f"{API}/colegio/estudiantes/{e['id']}").status_code == 204    # el dueño si puede retirarlo
    hechas = acciones("estudiante", e["id"])                                              # quedan auditadas
    assert sorted(hechas) == ["crear_estudiante", "retirar_estudiante"]


def test_estudiantes_obtener_y_editar():
    org1, org2, adm = organizador("org98@x.co", "898000001"), organizador("org99b@x.co", "898000002"), admin()
    col1, _ = colegio_de(org1, "rector98@x.co", "998000001")
    col2, _ = colegio_de(org2, "rector99@x.co", "998000002")
    e = col1.post(f"{API}/colegio/estudiantes", json={**EST, "documento": "1234567890"}).json()
    url = f"{API}/colegio/estudiantes/{e['id']}"
    # obtener: el propio si (documento enmascarado), el ajeno 404
    r = col1.get(url)
    assert r.status_code == 200 and r.json() == {"id": e["id"], "nombre": "Valentina", "apellido": "Rios", "documento": "123*****90", "grado": "9"}
    assert col2.get(url).status_code == 404 and col1.get(f"{API}/colegio/estudiantes/99999").status_code == 404
    # editar: cambia los datos, sale enmascarado, refresca "actualizado" y queda auditado
    cambio = dict(nombre="Valeria", apellido="Rios Paz", documento="1234567899", id_grado=1)
    r = col1.put(url, json=cambio)
    assert r.status_code == 200 and r.json()["nombre"] == "Valeria" and r.json()["documento"] == "123*****99"
    fila = sql("SELECT documento, creado, actualizado FROM estudiante WHERE id = %s", e["id"])[0]
    assert fila["documento"] == "1234567899" and fila["actualizado"] > fila["creado"]
    assert "editar_estudiante" in acciones("estudiante", e["id"])
    # editar el de otro colegio: 404 y no cambia nada
    assert col2.put(url, json={**cambio, "nombre": "Intruso"}).status_code == 404
    assert col1.get(url).json()["nombre"] == "Valeria"
    # grado inexistente o dado de baja: 422; campos extra: 422
    assert col1.put(url, json={**cambio, "id_grado": 999}).status_code == 422
    gid = adm.post(f"{API}/admin/catalogos/grados", json={"nombre": "Grado de baja"}).json()["id"]
    adm.delete(f"{API}/admin/catalogos/grados/{gid}")
    r = col1.put(url, json={**cambio, "id_grado": gid})
    assert r.status_code == 422 and r.json()["detail"] == "Grado inválido"
    assert col1.put(url, json={**cambio, "id_colegio": 2}).status_code == 422
    # documento repetido dentro del mismo colegio: 409
    otro = col1.post(f"{API}/colegio/estudiantes", json={**EST, "documento": "5555555555"}).json()
    assert col1.put(f"{API}/colegio/estudiantes/{otro['id']}", json=cambio).status_code == 409


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

from app.api.rutas_inscripciones import csv_seguro  # noqa: E402


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


def test_eventos_editar_eliminar_cerrar():
    org, adm = organizador("org70@x.co", "870000001"), admin()
    col, _ = colegio_de(org, "rector70@x.co", "970000001")
    eid = org.post(f"{API}/organizador/eventos", json=evento_json()).json()["id"]
    r = org.put(f"{API}/organizador/eventos/{eid}", json=evento_json(nombre="Feria editada"))
    assert r.status_code == 200 and r.json()["nombre"] == "Feria editada" and r.json()["estado"] == "borrador"
    assert org.put(f"{API}/organizador/eventos/{eid}", json=evento_json(id_ciudad=999)).status_code == 422
    assert org.delete(f"{API}/organizador/eventos/{eid}").status_code == 204                  # borrado logico
    assert all(e["id"] != eid for e in org.get(f"{API}/organizador/eventos").json())
    pendiente = org.post(f"{API}/organizador/eventos", json=evento_json()).json()["id"]
    org.post(f"{API}/organizador/eventos/{pendiente}/enviar")
    assert org.delete(f"{API}/organizador/eventos/{pendiente}").status_code == 409            # pendiente: no se borra
    rechazado = org.post(f"{API}/organizador/eventos", json=evento_json()).json()["id"]
    org.post(f"{API}/organizador/eventos/{rechazado}/enviar")
    adm.patch(f"{API}/admin/eventos/{rechazado}/decision", json={"decision": "rechazado"})
    assert org.delete(f"{API}/organizador/eventos/{rechazado}").status_code == 204            # rechazado: si
    eid = publicar(org, adm)
    assert org.delete(f"{API}/organizador/eventos/{eid}").status_code == 409                  # publicado: no se borra
    assert any(e["id"] == eid for e in adm.get(f"{API}/admin/eventos", params={"estado": "publicado"}).json())
    e1 = estudiante(col, "1700000001")
    col.post(f"{API}/colegio/eventos/{eid}/inscripcion", json={"estudiantes": [e1]})
    ev = col.get(f"{API}/colegio/eventos").json()[0]
    assert ev["mi_inscripcion"] == "pendiente" and ev["colegios_inscritos"] == 1
    assert adm.post(f"{API}/admin/eventos/{eid}/cerrar").json()["estado"] == "cerrado"
    assert adm.post(f"{API}/admin/eventos/{eid}/cerrar").status_code == 409
    assert org.delete(f"{API}/organizador/eventos/{eid}").status_code == 204                  # cerrado: si
    assert all(e["id"] != eid for e in org.get(f"{API}/organizador/eventos").json())
    hechas = acciones("evento", eid)                                              # quedan auditadas
    assert hechas == ["crear_evento", "enviar_evento", "evento_publicado", "evento_cerrado", "eliminar_evento"]
    assert sql("SELECT estado FROM evento WHERE id = %s", eid)[0]["estado"] is False                 # la fila sigue: borrado logico


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


def test_cupo_lleno():
    from concurrent.futures import ThreadPoolExecutor
    org, adm = organizador("org80@x.co", "880000001"), admin()
    cols = [colegio_de(org, f"rector8{n}@x.co", f"98000000{n}")[0] for n in range(7)]
    est = [estudiante(c, f"80000000{n}") for n, c in enumerate(cols)]
    # en orden: cupo de 2 colegios
    eid = publicar(org, adm, cupo_colegios=2)
    inscribir = lambda n, ev: cols[n].post(f"{API}/colegio/eventos/{ev}/inscripcion", json={"estudiantes": [est[n]]})
    assert inscribir(0, eid).status_code == 201 and inscribir(1, eid).status_code == 201
    r = inscribir(2, eid)
    assert r.status_code == 409 and r.json()["detail"] == "El evento no tiene cupos disponibles"
    rechazada = [i for i in org.get(f"{API}/organizador/inscripciones").json() if i["id_evento"] == eid][0]["id"]
    assert org.patch(f"{API}/organizador/inscripciones/{rechazada}", json={"estado": "rechazada"}).status_code == 200
    assert inscribir(2, eid).status_code == 201                                                   # el rechazo libero el cupo
    assert cols[2].get(f"{API}/colegio/inscripciones").json()[0]["estado"] == "pendiente"
    # al mismo tiempo: 4 colegios para 2 cupos -> SELECT ... FOR UPDATE deja entrar exactamente a 2
    eid2 = publicar(org, adm, cupo_colegios=2)
    with ThreadPoolExecutor(4) as hilos:
        codigos = list(hilos.map(lambda n: inscribir(n, eid2).status_code, range(3, 7)))
    assert sorted(codigos) == [201, 201, 409, 409]


def test_admin_aprueba_organizadores_y_ve_colegios():
    adm = admin()
    r = TestClient(app).post(f"{API}/auth/registro/organizador", json=dict(correo="pend@x.co", contrasena="Clave1234", nombre="Pia",
                                                                      apellido="Paz", nit="840000001", organizacion_nombre="Fundacion Pend"))
    assert r.status_code == 201
    o = next(o for o in adm.get(f"{API}/admin/organizadores").json() if o["nit"] == "840000001")
    assert o["activo"] is False                                                           # nace pendiente
    assert adm.patch(f"{API}/admin/organizadores/{o['id']}/activo", json={"activo": True}).json() == {"id": o["id"], "activo": True}
    assert adm.patch(f"{API}/admin/organizadores/99999/activo", json={"activo": True}).status_code == 404
    org = organizador("org95@x.co", "840000002")
    colegio_de(org, "rector95@x.co", "940000001")
    assert any(c["nit"] == "940000001" and c["activo"] for c in adm.get(f"{API}/admin/colegios").json())
    assert org.get(f"{API}/admin/organizadores").status_code == 403 and org.get(f"{API}/admin/colegios").status_code == 403
    hechas = acciones("organizador", o["id"])                                              # quedan auditadas
    assert hechas == ["registro_organizador", "activar_organizador"]


def test_resumen_del_administrador():
    adm, org = admin(), organizador("org96@x.co", "896000001")
    antes = adm.get(f"{API}/admin/resumen").json()
    assert set(antes) == {"eventos_por_estado", "colegios", "organizadores", "organizadores_pendientes", "inscripciones"}
    eid = org.post(f"{API}/organizador/eventos", json=evento_json()).json()["id"]
    assert adm.get(f"{API}/admin/resumen").json()["eventos_por_estado"]["borrador"] == antes["eventos_por_estado"].get("borrador", 0) + 1
    org.delete(f"{API}/organizador/eventos/{eid}")                                          # borrado logico: ya no cuenta
    assert adm.get(f"{API}/admin/resumen").json()["eventos_por_estado"]["borrador"] == antes["eventos_por_estado"].get("borrador", 0)
    assert org.get(f"{API}/admin/resumen").status_code == 403


def test_seguridad_de_auth():
    from app.core.config import settings
    PERFIL = {"id", "correo", "nombre", "apellido", "rol", "modulos", "id_colegio", "id_organizador"}
    adm = admin()
    # registro de organizador: queda pendiente (403) hasta que el administrador lo aprueba
    c = TestClient(app)
    r = c.post(f"{API}/auth/registro/organizador", json=dict(correo="Seg.Org@x.co", contrasena="Clave1234", nombre="Sara", apellido="Gil",
                                                             nit="850000001", organizacion_nombre="Fundacion Segura"))
    assert r.status_code == 201 and "aprobar" in r.json()["mensaje"]
    assert c.post(f"{API}/auth/registro/organizador", json=dict(correo="seg.org@x.co", contrasena="Clave1234", nombre="Sara", apellido="Gil",
                                                                nit="850000002", organizacion_nombre="Otra")).status_code == 409   # correo repetido
    login = lambda correo, clave="Clave1234": TestClient(app).post(f"{API}/auth/login", json={"correo": correo, "contrasena": clave})
    r = login("seg.org@x.co")
    assert r.status_code == 403 and r.json()["detail"] == "Tu cuenta está pendiente de aprobación o fue desactivada"
    oid = next(o["id"] for o in adm.get(f"{API}/admin/organizadores").json() if o["nit"] == "850000001")
    adm.patch(f"{API}/admin/organizadores/{oid}/activo", json={"activo": True})
    # login en los 3 roles: misma forma de respuesta que antes, y la cookie con sus atributos de seguridad
    settings.cookie_secure = True
    try:
        r = login("SEG.ORG@x.co")                                                     # el correo no distingue mayusculas
    finally:
        settings.cookie_secure = False
    assert r.status_code == 200 and set(r.json()) == PERFIL | {"access_token", "token_type"}
    assert r.json()["rol"] == "organizador" and r.json()["id_organizador"] and r.json()["token_type"] == "bearer"
    galleta = r.headers["set-cookie"].lower()
    assert "httponly" in galleta and "secure" in galleta and "samesite=lax" in galleta and "path=/" in galleta and "max-age=3600" in galleta
    assert set(adm.get(f"{API}/auth/me").json()) == PERFIL and adm.get(f"{API}/auth/me").json()["id_colegio"] is None
    col, id_col = colegio_de(organizador("org97@x.co", "897000001"), "rector97@x.co", "997000001")
    assert col.get(f"{API}/auth/me").json()["id_colegio"] == id_col
    # contrasena incorrecta, usuario que no existe: mismo mensaje (no revela si el correo existe)
    assert login("seg.org@x.co", "Mala12345").json() == login("nadie.nunca@x.co").json() == {"detail": "Correo o contraseña incorrectos"}
    # cambio de contrasena: con la actual mala 400; bien hecho, la vieja deja de servir
    org = TestClient(app)
    org.post(f"{API}/auth/login", json={"correo": "seg.org@x.co", "contrasena": "Clave1234"})
    assert org.post(f"{API}/auth/cambiar-contrasena", json={"actual": "Mala12345", "nueva": "Nueva12345"}).status_code == 400
    assert org.post(f"{API}/auth/cambiar-contrasena", json={"actual": "Clave1234", "nueva": "Nueva12345"}).status_code == 204
    assert login("seg.org@x.co").status_code == 401 and login("seg.org@x.co", "Nueva12345").status_code == 200
    # desactivado o eliminado: no entra y su sesion abierta deja de servir
    uid = org.get(f"{API}/auth/me").json()["id"]
    adm.patch(f"{API}/admin/organizadores/{oid}/activo", json={"activo": False})
    assert org.get(f"{API}/auth/me").status_code == 401 and login("seg.org@x.co", "Nueva12345").status_code == 403
    adm.patch(f"{API}/admin/organizadores/{oid}/activo", json={"activo": True})
    assert org.get(f"{API}/auth/me").status_code == 200
    assert adm.delete(f"{API}/admin/usuarios/{uid}").status_code == 200
    assert org.get(f"{API}/auth/me").status_code == 401 and login("seg.org@x.co", "Nueva12345").status_code == 401
    # cerrar sesion borra la cookie
    r = adm.post(f"{API}/auth/logout")
    assert r.status_code == 204 and 'token=""' in r.headers["set-cookie"] and "max-age=0" in r.headers["set-cookie"].lower()
    assert adm.get(f"{API}/auth/me").status_code == 401


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
    assert c.get("/ruta-inventada").status_code == 404 and c.get("/docs").status_code == 200  # Swagger habilitado (docs_habilitada=True)
    assert c.get("/api/v1/no-existe").status_code == 404
    assert c.get("/api/v1/catalogos/grados").headers["cache-control"] == "no-store"
    assert c.get("/login").headers["cache-control"] == "no-cache"
    assert "gzip" in c.get("/login", headers={"accept-encoding": "gzip"}).headers.get("content-encoding", "gzip")


# ---------------- Administracion de usuarios y roles ----------------
def test_admin_gestiona_usuarios_y_roles():
    from app.repositories.admin_repo import AdminRepository
    AdminRepository().asegurar_modulos_admin()
    AdminRepository().asegurar_modulos_admin()  # idempotente
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


def test_conteo_de_usuarios_por_rol_no_cuenta_eliminados():
    adm = admin()
    contar = lambda: next(r["usuarios"] for r in adm.get(f"{API}/admin/roles").json()["roles"] if r["nombre"] == "administrador")
    antes = contar()
    uid = adm.post(f"{API}/admin/usuarios", json=dict(correo="conteo@x.co", nombre="Ceci", apellido="Paz", rol="administrador")).json()["usuario"]["id"]
    assert contar() == antes + 1
    assert adm.delete(f"{API}/admin/usuarios/{uid}").status_code == 200
    assert contar() == antes                                                   # el eliminado (estado=false) ya no cuenta


def test_admin_elimina_usuario():
    adm = admin()
    uid = adm.post(f"{API}/admin/usuarios", json=dict(correo="borrar@x.co", nombre="Beto", apellido="Ruiz", rol="administrador")).json()["usuario"]["id"]
    assert adm.delete(f"{API}/admin/usuarios/1").status_code == 409          # a si mismo no
    assert adm.delete(f"{API}/admin/usuarios/{uid}").status_code == 200
    assert adm.delete(f"{API}/admin/usuarios/{uid}").status_code == 404
    # un organizador sin eventos se borra junto con su perfil
    oid = adm.post(f"{API}/admin/usuarios", json=dict(correo="borrar2@x.co", nombre="Beto", apellido="Ruiz", rol="organizador",
                                                      organizacion_nombre="Fund Borrar", nit="820000077")).json()["usuario"]["id"]
    assert adm.delete(f"{API}/admin/usuarios/{oid}").status_code == 200
    assert adm.get(f"{API}/admin/usuarios", params={"q": "borrar"}).json() == []
    assert organizador("org99@x.co", "820000099").delete(f"{API}/admin/usuarios/{uid}").status_code == 403


def test_organizador_elimina_colegio():
    org1, org2, adm = organizador("org30@x.co", "830000001"), organizador("org31@x.co", "830000002"), admin()
    col, id1 = colegio_de(org1, "rector30@x.co", "930000001")
    estudiante(col, "2000000001")
    assert org2.delete(f"{API}/organizador/colegios/{id1}").status_code == 404           # no es suyo
    assert col.delete(f"{API}/organizador/colegios/{id1}").status_code == 403            # un colegio no elimina
    eid = publicar(org1, adm)
    col.post(f"{API}/colegio/eventos/{eid}/inscripcion", json={"estudiantes": [1]})
    id2 = colegio_de(org1, "rector31@x.co", "930000002")[1]
    assert org1.delete(f"{API}/organizador/colegios/{id2}").status_code == 204           # baja logica
    assert all(c["id"] != id2 for c in org1.get(f"{API}/organizador/colegios").json())
    assert sql("SELECT estado FROM colegio WHERE id = %s", id2)[0]["estado"] is False      # la fila sigue en la tabla, con estado=False
    assert org1.delete(f"{API}/organizador/colegios/{id2}").status_code == 404           # ya eliminado
    assert org1.delete(f"{API}/organizador/colegios/{id1}").status_code == 204           # con inscripciones tambien: se conserva el historial


# ---------------- Taller: estado / creado / actualizado, JWT Bearer, CRUD de catalogos ----------------
def test_todas_las_tablas_tienen_estado_creado_actualizado():
    columnas = sql("""SELECT table_name, column_name, is_nullable FROM information_schema.columns
                      WHERE table_schema = 'public' AND column_name IN ('estado', 'creado', 'actualizado')""")
    tablas = {f["table_name"] for f in sql("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")}
    assert len(tablas) == 18
    for t in tablas:
        propias = {f["column_name"]: f["is_nullable"] for f in columnas if f["table_name"] == t}
        assert propias == {"estado": "NO", "creado": "NO", "actualizado": "NO"}, f"{t}: {propias}"
    defaults = {(f["table_name"], f["column_name"]): f["column_default"] for f in sql(
        "SELECT table_name, column_name, column_default FROM information_schema.columns WHERE table_schema = 'public'")}
    assert defaults[("usuario", "activo")] == "true" and defaults[("autorizacion_acudiente", "vigente")] == "true"
    assert defaults[("inscripcion_estudiante", "asistio")] == "false"


def test_creado_actualizado_y_estado_por_defecto():
    import time
    adm = admin()
    r = adm.post(f"{API}/admin/catalogos/grados", json={"nombre": "Aud-1"})
    assert r.status_code == 201 and r.json()["estado"] is True and r.json()["creado"] and r.json()["actualizado"]
    antes = r.json()["actualizado"]
    time.sleep(1.1)
    r2 = adm.put(f"{API}/admin/catalogos/grados/{r.json()['id']}", json={"nombre": "Aud-2"})
    assert r2.json()["creado"] == r.json()["creado"] and r2.json()["actualizado"] > antes     # creado fijo, actualizado cambia


def test_crud_catalogo_con_baja_logica():
    adm = admin()
    gid = adm.post(f"{API}/admin/catalogos/grados", json={"nombre": "Soft-1"}).json()["id"]
    assert adm.post(f"{API}/admin/catalogos/grados", json={"nombre": "Soft-1"}).status_code == 409   # campo unico
    assert adm.post(f"{API}/admin/catalogos/grados", json={}).status_code == 422
    assert adm.post(f"{API}/admin/catalogos/grados", json={"nombre": "x", "estado": False}).status_code == 422  # estado no se envia al crear
    assert adm.post(f"{API}/admin/catalogos/nada", json={"nombre": "x"}).status_code == 404
    assert any(g["id"] == gid for g in adm.get(f"{API}/catalogos/grados").json())
    assert adm.delete(f"{API}/admin/catalogos/grados/{gid}").json()["estado"] is False                 # baja logica
    assert all(g["id"] != gid for g in adm.get(f"{API}/catalogos/grados").json())                       # ya no se ofrece
    assert any(g["id"] == gid for g in adm.get(f"{API}/admin/catalogos/grados", params={"todos": True}).json())  # pero la fila existe
    assert adm.patch(f"{API}/admin/catalogos/grados/{gid}/estado", json={"estado": True}).json()["estado"] is True  # restaurar
    assert adm.delete(f"{API}/admin/catalogos/roles/1").status_code == 409                              # rol administrador protegido
    assert organizador("org60@x.co", "860000001").get(f"{API}/admin/catalogos/grados").status_code == 403


def test_jwt_bearer_y_validacion():
    c = TestClient(app)
    r = c.post(f"{API}/auth/login", json={"correo": "admin@x.co", "contrasena": "Admin1234"})
    token = r.json()["access_token"]
    assert r.json()["token_type"] == "bearer" and token.count(".") == 2                      # JWT: cabecera.carga.firma
    limpio = TestClient(app)                                                                  # sin cookie: solo la cabecera
    assert limpio.get(f"{API}/auth/me").status_code == 401                                    # sin token
    assert limpio.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"}).json()["rol"] == "administrador"
    assert limpio.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token[:-2]}xx"}).status_code == 401   # firma alterada
    import jwt as pyjwt
    from datetime import datetime, timedelta, timezone
    vencido = pyjwt.encode({"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}, "test-secret", algorithm="HS256")
    assert limpio.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {vencido}"}).status_code == 401       # expirado
    ajeno = pyjwt.encode({"sub": "1"}, "otra-clave", algorithm="HS256")
    assert limpio.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {ajeno}"}).status_code == 401         # firmado con otra clave
    assert pyjwt.decode(token, "test-secret", algorithms=["HS256"])["rol"] == "administrador"


def test_swagger_publicado():
    c = TestClient(app)
    assert c.get("/docs").status_code == 200 and "/api/v1/auth/login" in c.get("/openapi.json").text
