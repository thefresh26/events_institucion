-- ============================================================================
-- Conexion Escolar - esquema PostgreSQL (18 tablas). Generado a partir de los modelos que habia en
-- app/models (SQLAlchemy) antes de quitarlo, para crear una base NUEVA igual a la de Neon.
-- Lo usan scripts/inicializar_bd.py y las pruebas. Idempotente (IF NOT EXISTS).
-- Todas las tablas llevan estado (borrado logico), creado y actualizado (+ trigger trg_actualizado).
-- ============================================================================

CREATE TABLE IF NOT EXISTS categoria_evento (
	id SERIAL NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	descripcion VARCHAR(255), 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nombre)
);

CREATE TABLE IF NOT EXISTS departamento (
	id SERIAL NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nombre)
);

CREATE TABLE IF NOT EXISTS estado_evento (
	id SERIAL NOT NULL, 
	nombre VARCHAR(30) NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nombre)
);

CREATE TABLE IF NOT EXISTS estado_inscripcion (
	id SERIAL NOT NULL, 
	nombre VARCHAR(30) NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nombre)
);

CREATE TABLE IF NOT EXISTS grado (
	id SERIAL NOT NULL, 
	nombre VARCHAR(20) NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nombre)
);

CREATE TABLE IF NOT EXISTS modulo (
	id SERIAL NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	descripcion VARCHAR(255), 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nombre)
);

CREATE TABLE IF NOT EXISTS rol (
	id SERIAL NOT NULL, 
	nombre VARCHAR(50) NOT NULL, 
	descripcion VARCHAR(255), 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nombre)
);

CREATE TABLE IF NOT EXISTS ciudad (
	id SERIAL NOT NULL, 
	id_departamento INTEGER NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (id_departamento, nombre), 
	FOREIGN KEY(id_departamento) REFERENCES departamento (id)
);

CREATE TABLE IF NOT EXISTS modulo_por_rol (
	id SERIAL NOT NULL, 
	id_rol INTEGER NOT NULL, 
	id_modulo INTEGER NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (id_rol, id_modulo), 
	FOREIGN KEY(id_rol) REFERENCES rol (id), 
	FOREIGN KEY(id_modulo) REFERENCES modulo (id)
);

CREATE TABLE IF NOT EXISTS usuario (
	id SERIAL NOT NULL, 
	id_rol INTEGER NOT NULL, 
	correo VARCHAR(255) NOT NULL, 
	contrasena VARCHAR(255) NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	apellido VARCHAR(100) NOT NULL, 
	activo BOOLEAN DEFAULT true NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id_rol) REFERENCES rol (id), 
	UNIQUE (correo)
);

CREATE TABLE IF NOT EXISTS auditoria (
	id SERIAL NOT NULL, 
	id_usuario INTEGER, 
	accion VARCHAR(100) NOT NULL, 
	tabla VARCHAR(60), 
	registro_id INTEGER, 
	ip VARCHAR(45), 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id_usuario) REFERENCES usuario (id)
);

CREATE TABLE IF NOT EXISTS organizador (
	id SERIAL NOT NULL, 
	id_usuario INTEGER NOT NULL, 
	nombre VARCHAR(150) NOT NULL, 
	nit VARCHAR(20) NOT NULL, 
	telefono VARCHAR(20), 
	descripcion VARCHAR(255), 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (id_usuario), 
	FOREIGN KEY(id_usuario) REFERENCES usuario (id), 
	UNIQUE (nit)
);

CREATE TABLE IF NOT EXISTS colegio (
	id SERIAL NOT NULL, 
	id_usuario INTEGER NOT NULL, 
	id_ciudad INTEGER NOT NULL, 
	id_organizador INTEGER NOT NULL, 
	nombre VARCHAR(150) NOT NULL, 
	nit VARCHAR(20) NOT NULL, 
	direccion VARCHAR(200), 
	telefono VARCHAR(20), 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (id_usuario), 
	FOREIGN KEY(id_usuario) REFERENCES usuario (id), 
	FOREIGN KEY(id_ciudad) REFERENCES ciudad (id), 
	FOREIGN KEY(id_organizador) REFERENCES organizador (id), 
	UNIQUE (nit)
);

CREATE TABLE IF NOT EXISTS evento (
	id SERIAL NOT NULL, 
	id_organizador INTEGER NOT NULL, 
	id_categoria INTEGER NOT NULL, 
	id_ciudad INTEGER NOT NULL, 
	id_estado INTEGER NOT NULL, 
	id_aprobador INTEGER, 
	nombre VARCHAR(150) NOT NULL, 
	descripcion VARCHAR(500), 
	lugar VARCHAR(150) NOT NULL, 
	fecha_inicio TIMESTAMP WITH TIME ZONE NOT NULL, 
	fecha_fin TIMESTAMP WITH TIME ZONE, 
	cupo_colegios INTEGER NOT NULL CHECK (cupo_colegios > 0), 
	cupo_estudiantes INTEGER NOT NULL CHECK (cupo_estudiantes > 0), 
	fecha_aprobacion TIMESTAMP WITH TIME ZONE, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id_organizador) REFERENCES organizador (id), 
	FOREIGN KEY(id_categoria) REFERENCES categoria_evento (id), 
	FOREIGN KEY(id_ciudad) REFERENCES ciudad (id), 
	FOREIGN KEY(id_estado) REFERENCES estado_evento (id), 
	FOREIGN KEY(id_aprobador) REFERENCES usuario (id)
);

CREATE TABLE IF NOT EXISTS estudiante (
	id SERIAL NOT NULL, 
	id_colegio INTEGER NOT NULL, 
	id_grado INTEGER NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	apellido VARCHAR(100) NOT NULL, 
	documento VARCHAR(20) NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (id_colegio, documento), 
	FOREIGN KEY(id_colegio) REFERENCES colegio (id), 
	FOREIGN KEY(id_grado) REFERENCES grado (id)
);

CREATE TABLE IF NOT EXISTS inscripcion (
	id SERIAL NOT NULL, 
	id_evento INTEGER NOT NULL, 
	id_colegio INTEGER NOT NULL, 
	id_estado INTEGER NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (id_evento, id_colegio), 
	FOREIGN KEY(id_evento) REFERENCES evento (id), 
	FOREIGN KEY(id_colegio) REFERENCES colegio (id), 
	FOREIGN KEY(id_estado) REFERENCES estado_inscripcion (id)
);

CREATE TABLE IF NOT EXISTS autorizacion_acudiente (
	id SERIAL NOT NULL, 
	id_estudiante INTEGER NOT NULL, 
	nombre_acudiente VARCHAR(150) NOT NULL, 
	fecha TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	vigente BOOLEAN DEFAULT true NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (id_estudiante), 
	FOREIGN KEY(id_estudiante) REFERENCES estudiante (id)
);

CREATE TABLE IF NOT EXISTS inscripcion_estudiante (
	id SERIAL NOT NULL, 
	id_inscripcion INTEGER NOT NULL, 
	id_estudiante INTEGER NOT NULL, 
	asistio BOOLEAN DEFAULT false NOT NULL, 
	estado BOOLEAN DEFAULT true NOT NULL, 
	creado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (id_inscripcion, id_estudiante), 
	FOREIGN KEY(id_inscripcion) REFERENCES inscripcion (id), 
	FOREIGN KEY(id_estudiante) REFERENCES estudiante (id)
);


-- actualizado = now() en cada UPDATE, en todas las tablas
CREATE OR REPLACE FUNCTION set_actualizado() RETURNS trigger AS $$
BEGIN NEW.actualizado = now(); RETURN NEW; END; $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_actualizado ON "categoria_evento";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "categoria_evento" FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_actualizado ON "departamento";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "departamento" FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_actualizado ON "estado_evento";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "estado_evento" FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_actualizado ON "estado_inscripcion";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "estado_inscripcion" FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_actualizado ON "grado";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "grado" FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_actualizado ON "modulo";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "modulo" FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_actualizado ON "rol";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "rol" FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_actualizado ON "ciudad";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "ciudad" FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_actualizado ON "modulo_por_rol";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "modulo_por_rol" FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_actualizado ON "usuario";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "usuario" FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_actualizado ON "auditoria";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "auditoria" FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_actualizado ON "organizador";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "organizador" FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_actualizado ON "colegio";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "colegio" FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_actualizado ON "evento";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "evento" FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_actualizado ON "estudiante";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "estudiante" FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_actualizado ON "inscripcion";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "inscripcion" FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_actualizado ON "autorizacion_acudiente";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "autorizacion_acudiente" FOR EACH ROW EXECUTE FUNCTION set_actualizado();

DROP TRIGGER IF EXISTS trg_actualizado ON "inscripcion_estudiante";
CREATE TRIGGER trg_actualizado BEFORE UPDATE ON "inscripcion_estudiante" FOR EACH ROW EXECUTE FUNCTION set_actualizado();
