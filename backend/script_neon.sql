-- ============================================================================
-- Conexion Escolar - script_neon.sql (PostgreSQL / Neon)
-- Esquema de 18 tablas (todas con estado, creado, actualizado + trigger) y datos de ejemplo realistas:
-- 20 registros o mas en las tablas principales y 10 o mas en las secundarias (los catalogos
-- cerrados rol=3, estado_evento=5 y estado_inscripcion=3 tienen los valores que el sistema define).
-- Escrito a mano para el taller (NO es un backup). Se puede ejecutar varias veces: no duplica.
-- Usuarios de ejemplo: todos con la misma clave de demostracion (se entrega aparte), guardada como hash bcrypt.
-- Orden: 1) esquema  2) catalogos  3) usuarios  4) organizadores y colegios  5) eventos  6) estudiantes
--        7) inscripciones  8) auditoria  9) ajuste de secuencias
-- ============================================================================

-- 1) ESQUEMA ------------------------------------------------------------
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

-- 2) CATALOGOS ----------------------------------------------------------

-- rol: 3 registros
INSERT INTO rol (id, nombre, descripcion) VALUES
  (1, 'administrador', 'Aprueba eventos y administra organizadores y colegios'),
  (2, 'organizador', 'Crea eventos y gestiona la inscripcion de colegios'),
  (3, 'colegio', 'Inscribe a su institucion y a sus estudiantes en los eventos')
ON CONFLICT DO NOTHING;

-- modulo: 12 registros
INSERT INTO modulo (id, nombre, descripcion) VALUES
  (1, 'panel', 'Resumen general'),
  (2, 'aprobar_eventos', 'Revisar y aprobar eventos pendientes'),
  (3, 'organizadores', 'Gestion de organizadores'),
  (4, 'colegios', 'Gestion de colegios'),
  (5, 'mis_eventos', 'Eventos del organizador'),
  (6, 'mis_colegios', 'Colegios vinculados al organizador'),
  (7, 'inscripciones', 'Solicitudes de inscripcion recibidas'),
  (8, 'asistencia', 'Control de asistencia'),
  (9, 'reportes', 'Reportes del organizador'),
  (10, 'eventos_disponibles', 'Eventos abiertos para inscripcion'),
  (11, 'mis_inscripciones', 'Inscripciones del colegio'),
  (12, 'mis_estudiantes', 'Estudiantes del colegio')
ON CONFLICT DO NOTHING;

-- modulo_por_rol: 14 registros
INSERT INTO modulo_por_rol (id_rol, id_modulo) VALUES
  (1, 1),
  (1, 2),
  (1, 3),
  (1, 4),
  (2, 1),
  (2, 5),
  (2, 6),
  (2, 7),
  (2, 8),
  (2, 9),
  (3, 1),
  (3, 10),
  (3, 11),
  (3, 12)
ON CONFLICT DO NOTHING;

-- departamento: 10 registros
INSERT INTO departamento (id, nombre) VALUES
  (1, 'Cundinamarca'),
  (2, 'Antioquia'),
  (3, 'Valle del Cauca'),
  (4, 'Atlántico'),
  (5, 'Santander'),
  (6, 'Bolívar'),
  (7, 'Boyacá'),
  (8, 'Risaralda'),
  (9, 'Caldas'),
  (10, 'Nariño')
ON CONFLICT DO NOTHING;

-- ciudad: 21 registros
INSERT INTO ciudad (id, id_departamento, nombre) VALUES
  (1, 1, 'Bogotá'),
  (2, 1, 'Soacha'),
  (3, 1, 'Zipaquirá'),
  (4, 2, 'Medellín'),
  (5, 2, 'Envigado'),
  (6, 3, 'Cali'),
  (7, 3, 'Palmira'),
  (8, 4, 'Barranquilla'),
  (9, 4, 'Soledad'),
  (10, 5, 'Bucaramanga'),
  (11, 5, 'Floridablanca'),
  (12, 6, 'Cartagena'),
  (13, 6, 'Magangué'),
  (14, 7, 'Tunja'),
  (15, 7, 'Duitama'),
  (16, 8, 'Pereira'),
  (17, 8, 'Dosquebradas'),
  (18, 9, 'Manizales'),
  (19, 9, 'Villamaría'),
  (20, 10, 'Pasto'),
  (21, 10, 'Ipiales')
ON CONFLICT DO NOTHING;

-- grado: 12 registros
INSERT INTO grado (id, nombre) VALUES
  (1, 'Preescolar'),
  (2, '1'),
  (3, '2'),
  (4, '3'),
  (5, '4'),
  (6, '5'),
  (7, '6'),
  (8, '7'),
  (9, '8'),
  (10, '9'),
  (11, '10'),
  (12, '11')
ON CONFLICT DO NOTHING;

-- categoria_evento: 10 registros
INSERT INTO categoria_evento (id, nombre, descripcion) VALUES
  (1, 'Ciencia', 'Ferias y olimpiadas de ciencias naturales'),
  (2, 'Deporte', 'Torneos e intercolegiados deportivos'),
  (3, 'Cultura', 'Muestras artisticas y folclor'),
  (4, 'Tecnología', 'Robotica, programacion e innovacion'),
  (5, 'Académico', 'Concursos de conocimiento y debates'),
  (6, 'Ambiental', 'Jornadas ecologicas y reciclaje'),
  (7, 'Matemáticas', 'Olimpiadas y retos matematicos'),
  (8, 'Lectura y escritura', 'Concursos literarios y de oratoria'),
  (9, 'Emprendimiento', 'Ferias de emprendimiento juvenil'),
  (10, 'Música', 'Festivales y encuentros musicales')
ON CONFLICT DO NOTHING;

-- estado_evento: 5 registros
INSERT INTO estado_evento (id, nombre) VALUES
  (1, 'borrador'),
  (2, 'pendiente'),
  (3, 'publicado'),
  (4, 'rechazado'),
  (5, 'cerrado')
ON CONFLICT DO NOTHING;

-- estado_inscripcion: 3 registros
INSERT INTO estado_inscripcion (id, nombre) VALUES
  (1, 'pendiente'),
  (2, 'aceptada'),
  (3, 'rechazada')
ON CONFLICT DO NOTHING;

-- 3) USUARIOS (1 administrador demo, 20 organizadores, 20 colegios) --------
-- Si ya existe el correo, no se toca (asi se conservan los usuarios reales del sistema).

-- usuario: 41 registros
INSERT INTO usuario (id, id_rol, correo, contrasena, nombre, apellido) VALUES
  (1, 1, 'admin.demo@conexionescolar.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Andrea', 'Villamizar'),
  (2, 2, 'contacto01@fundacion.ciencia.vi.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Camila', 'Rodríguez'),
  (3, 2, 'contacto02@corporacion.deportiv.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Santiago', 'Gómez'),
  (4, 2, 'contacto03@fundacion.cultural.r.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Valentina', 'Martínez'),
  (5, 2, 'contacto04@tecnoeduca.sas.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Mateo', 'López'),
  (6, 2, 'contacto05@liga.academica.del.c.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Sofía', 'García'),
  (7, 2, 'contacto06@fundacion.verde.futu.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Juan David', 'Hernández'),
  (8, 2, 'contacto07@instituto.matematico.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Isabella', 'Ramírez'),
  (9, 2, 'contacto08@corporacion.letras.l.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Samuel', 'Torres'),
  (10, 2, 'contacto09@fundacion.semillas.d.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Mariana', 'Vargas'),
  (11, 2, 'contacto10@casa.de.la.musica.an.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Daniel', 'Castro'),
  (12, 2, 'contacto11@fundacion.horizonte.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Laura', 'Rojas'),
  (13, 2, 'contacto12@club.deportivo.los.c.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Andrés', 'Moreno'),
  (14, 2, 'contacto13@corporacion.arte.jov.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Luciana', 'Jiménez'),
  (15, 2, 'contacto14@fundacion.codigo.abi.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Sebastián', 'Ortiz'),
  (16, 2, 'contacto15@asociacion.debate.co.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Gabriela', 'Suárez'),
  (17, 2, 'contacto16@fundacion.planeta.az.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Nicolás', 'Pardo'),
  (18, 2, 'contacto17@academia.pitagoras.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Daniela', 'Cárdenas'),
  (19, 2, 'contacto18@fundacion.tinta.y.pa.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Felipe', 'Mejía'),
  (20, 2, 'contacto19@red.emprende.boyaca.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Salomé', 'Osorio'),
  (21, 2, 'contacto20@orquesta.escolar.del.org', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Tomás', 'Arango'),
  (22, 3, 'rectoria01@colegio.san.jose.de.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Samuel', 'López'),
  (23, 3, 'rectoria02@gimnasio.moderno.del.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Mariana', 'García'),
  (24, 3, 'rectoria03@instituto.tecnico.in.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Daniel', 'Hernández'),
  (25, 3, 'rectoria04@colegio.nuestra.seno.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Laura', 'Ramírez'),
  (26, 3, 'rectoria05@liceo.francisco.de.p.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Andrés', 'Torres'),
  (27, 3, 'rectoria06@colegio.biling.e.los.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Luciana', 'Vargas'),
  (28, 3, 'rectoria07@institucion.educativ.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Sebastián', 'Castro'),
  (29, 3, 'rectoria08@colegio.departamenta.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Gabriela', 'Rojas'),
  (30, 3, 'rectoria09@gimnasio.campestre.l.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Nicolás', 'Moreno'),
  (31, 3, 'rectoria10@colegio.camilo.torre.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Daniela', 'Jiménez'),
  (32, 3, 'rectoria11@instituto.pedagogico.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Felipe', 'Ortiz'),
  (33, 3, 'rectoria12@colegio.santa.teresa.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Salomé', 'Suárez'),
  (34, 3, 'rectoria13@institucion.educativ.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Tomás', 'Pardo'),
  (35, 3, 'rectoria14@colegio.la.salle.cen.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Camila', 'Cárdenas'),
  (36, 3, 'rectoria15@liceo.moderno.benjam.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Santiago', 'Mejía'),
  (37, 3, 'rectoria16@colegio.gimnasio.del.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Valentina', 'Osorio'),
  (38, 3, 'rectoria17@institucion.educativ.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Mateo', 'Arango'),
  (39, 3, 'rectoria18@colegio.cooperativo.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Sofía', 'Quintero'),
  (40, 3, 'rectoria19@colegio.mayor.de.san.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Juan David', 'Salazar'),
  (41, 3, 'rectoria20@instituto.integrado.edu.co', '$2b$10$JtvUjislG7yjfJDiKr6Mc.Hea5NMuehTtHrgJswzO5susLK6Yugxy', 'Isabella', 'Rodríguez')
ON CONFLICT DO NOTHING;

-- 4) ORGANIZADORES (20) Y COLEGIOS (20) -------------------------------

-- organizador: 20 registros
INSERT INTO organizador (id, id_usuario, nombre, nit, telefono, descripcion) VALUES
  (1, 2, 'Fundación Ciencia Viva', '900000100-0', '6013000000', 'Divulgacion cientifica para jovenes'),
  (2, 3, 'Corporación Deportiva Altius', '900000107-1', '6023137531', 'Torneos intercolegiados'),
  (3, 4, 'Fundación Cultural Raíces', '900000115-2', '6033275062', 'Folclor y artes escenicas'),
  (4, 5, 'Tecnoeduca SAS', '900000123-3', '6043412593', 'Robotica y programacion escolar'),
  (5, 6, 'Liga Académica del Caribe', '900000131-4', '6053550124', 'Concursos de conocimiento'),
  (6, 7, 'Fundación Verde Futuro', '900000139-5', '6063687655', 'Educacion ambiental'),
  (7, 8, 'Instituto Matemático Gauss', '900000147-6', '6073825186', 'Olimpiadas matematicas'),
  (8, 9, 'Corporación Letras Libres', '900000155-7', '6083962717', 'Fomento de lectura y escritura'),
  (9, 10, 'Fundación Semillas de Emprendimiento', '900000163-8', '6014100248', 'Emprendimiento juvenil'),
  (10, 11, 'Casa de la Música Andina', '900000171-9', '6024237779', 'Encuentros musicales escolares'),
  (11, 12, 'Fundación Horizonte Científico', '900000179-0', '6034375310', 'Ferias de ciencia'),
  (12, 13, 'Club Deportivo Los Cerros', '900000187-1', '6044512841', 'Atletismo y natacion escolar'),
  (13, 14, 'Corporación Arte Joven', '900000195-2', '6054650372', 'Pintura y muralismo'),
  (14, 15, 'Fundación Código Abierto', '900000102-3', '6064787903', 'Software libre en colegios'),
  (15, 16, 'Asociación Debate Colombia', '900000110-4', '6074925434', 'Debate y oratoria'),
  (16, 17, 'Fundación Planeta Azul', '900000118-5', '6085062965', 'Cuidado del agua'),
  (17, 18, 'Academia Pitágoras', '900000126-6', '6015200496', 'Retos logicos y matematicos'),
  (18, 19, 'Fundación Tinta y Papel', '900000134-7', '6025338027', 'Talleres literarios'),
  (19, 20, 'Red Emprende Boyacá', '900000142-8', '6035475558', 'Ferias empresariales escolares'),
  (20, 21, 'Orquesta Escolar del Pacífico', '900000150-9', '6045613089', 'Orquestas y bandas juveniles')
ON CONFLICT DO NOTHING;

-- colegio: 20 registros
INSERT INTO colegio (id, id_usuario, id_ciudad, id_organizador, nombre, nit, direccion, telefono) VALUES
  (1, 22, 1, 1, 'Colegio San José de Calasanz', '800000200-4', 'Cra 7 # 45-12', '6077125930'),
  (2, 23, 1, 2, 'Gimnasio Moderno del Norte', '800000207-5', 'Calle 80 # 20-30', '6087263461'),
  (3, 24, 2, 3, 'Instituto Técnico Industrial Simón Bolívar', '800000215-6', 'Av. Las Palmas # 15-50', '6017400992'),
  (4, 25, 4, 4, 'Colegio Nuestra Señora del Rosario', '800000223-7', 'Cra 15 # 100-20', '6027538523'),
  (5, 26, 5, 5, 'Liceo Francisco de Paula Santander', '800000231-8', 'Calle 5 # 38-22', '6037676054'),
  (6, 27, 6, 6, 'Colegio Bilingüe Los Andes', '800000239-9', 'Cra 7 # 45-12', '6047813585'),
  (7, 28, 7, 7, 'Institución Educativa La Esperanza', '800000247-0', 'Calle 80 # 20-30', '6057951116'),
  (8, 29, 8, 8, 'Colegio Departamental Antonio Nariño', '800000255-1', 'Av. Las Palmas # 15-50', '6068088647'),
  (9, 30, 9, 9, 'Gimnasio Campestre Los Almendros', '800000263-2', 'Cra 15 # 100-20', '6078226178'),
  (10, 31, 10, 10, 'Colegio Camilo Torres Restrepo', '800000271-3', 'Calle 5 # 38-22', '6088363709'),
  (11, 32, 11, 11, 'Instituto Pedagógico San Ignacio', '800000279-4', 'Cra 7 # 45-12', '6018501240'),
  (12, 33, 12, 12, 'Colegio Santa Teresa de Jesús', '800000287-5', 'Calle 80 # 20-30', '6028638771'),
  (13, 34, 13, 13, 'Institución Educativa Técnica Agropecuaria', '800000295-6', 'Av. Las Palmas # 15-50', '6038776302'),
  (14, 35, 14, 14, 'Colegio La Salle Centro', '800000202-7', 'Cra 15 # 100-20', '6048913833'),
  (15, 36, 15, 15, 'Liceo Moderno Benjamín Herrera', '800000210-8', 'Calle 5 # 38-22', '6059051364'),
  (16, 37, 16, 16, 'Colegio Gimnasio del Pacífico', '800000218-9', 'Cra 7 # 45-12', '6069188895'),
  (17, 38, 17, 17, 'Institución Educativa Policarpa Salavarrieta', '800000226-0', 'Calle 80 # 20-30', '6079326426'),
  (18, 39, 18, 18, 'Colegio Cooperativo Rafael Uribe', '800000234-1', 'Av. Las Palmas # 15-50', '6089463957'),
  (19, 40, 20, 19, 'Colegio Mayor de San Bartolomé', '800000242-2', 'Cra 15 # 100-20', '6019601488'),
  (20, 41, 3, 20, 'Instituto Integrado Jorge Eliécer Gaitán', '800000250-3', 'Calle 5 # 38-22', '6029739019')
ON CONFLICT DO NOTHING;

-- 5) EVENTOS (20) -------------------------------------------------------

-- evento: 20 registros
INSERT INTO evento (id, id_organizador, id_categoria, id_ciudad, id_estado, id_aprobador, nombre, descripcion, lugar, fecha_inicio, fecha_fin, cupo_colegios, cupo_estudiantes, fecha_aprobacion) VALUES
  (1, 1, 1, 1, 3, 1, 'Feria Nacional de Ciencias 2026', 'Feria Nacional de Ciencias 2026: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Corferias, Pabellón 6', '2026-10-05 08:00:00-05'::timestamptz, '2026-10-05 16:00:00-05'::timestamptz, 8, 40, '2026-07-10 10:30:00-05'::timestamptz),
  (2, 2, 2, 4, 3, 1, 'Intercolegiado de Atletismo Antioquia', 'Intercolegiado de Atletismo Antioquia: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Estadio Atanasio Girardot', '2026-11-08 08:00:00-05'::timestamptz, '2026-11-08 16:00:00-05'::timestamptz, 12, 60, '2026-08-11 10:30:00-05'::timestamptz),
  (3, 3, 3, 6, 3, 1, 'Festival Folclórico Estudiantil', 'Festival Folclórico Estudiantil: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Teatro Municipal Enrique Buenaventura', '2026-12-11 08:00:00-05'::timestamptz, '2026-12-11 16:00:00-05'::timestamptz, 16, 80, '2026-07-12 10:30:00-05'::timestamptz),
  (4, 4, 4, 1, 3, 1, 'Torneo de Robótica Escolar', 'Torneo de Robótica Escolar: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Universidad Nacional, Edificio Uriel Gutiérrez', '2026-10-14 08:00:00-05'::timestamptz, '2026-10-14 16:00:00-05'::timestamptz, 20, 100, '2026-08-13 10:30:00-05'::timestamptz),
  (5, 5, 5, 8, 3, 1, 'Olimpiadas del Conocimiento del Caribe', 'Olimpiadas del Conocimiento del Caribe: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Universidad del Norte', '2026-11-17 08:00:00-05'::timestamptz, '2026-11-17 16:00:00-05'::timestamptz, 8, 120, '2026-07-14 10:30:00-05'::timestamptz),
  (6, 6, 6, 10, 3, 1, 'Jornada Ecológica Páramo Vivo', 'Jornada Ecológica Páramo Vivo: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Parque Nacional del Chicamocha', '2026-12-20 08:00:00-05'::timestamptz, '2026-12-20 16:00:00-05'::timestamptz, 12, 40, '2026-08-15 10:30:00-05'::timestamptz),
  (7, 7, 7, 4, 5, 1, 'Olimpiada Regional de Matemáticas', 'Olimpiada Regional de Matemáticas: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Universidad EAFIT', '2026-08-23 08:00:00-05'::timestamptz, '2026-08-23 16:00:00-05'::timestamptz, 16, 60, '2026-07-16 10:30:00-05'::timestamptz),
  (8, 8, 8, 14, 2, NULL, 'Concurso de Cuento y Oratoria', 'Concurso de Cuento y Oratoria: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Casa del Fundador', '2026-11-26 08:00:00-05'::timestamptz, '2026-11-26 16:00:00-05'::timestamptz, 20, 80, NULL),
  (9, 9, 9, 16, 3, 1, 'Feria Escolar de Emprendimiento', 'Feria Escolar de Emprendimiento: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Centro de Convenciones Expofuturo', '2026-12-07 08:00:00-05'::timestamptz, '2026-12-07 16:00:00-05'::timestamptz, 8, 100, '2026-07-18 10:30:00-05'::timestamptz),
  (10, 10, 10, 20, 2, NULL, 'Encuentro de Bandas Andinas', 'Encuentro de Bandas Andinas: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Teatro Imperial', '2026-10-10 08:00:00-05'::timestamptz, '2026-10-10 16:00:00-05'::timestamptz, 12, 120, NULL),
  (11, 11, 1, 12, 5, 1, 'Expociencia Cartagena', 'Expociencia Cartagena: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Centro de Convenciones Getsemaní', '2026-08-13 08:00:00-05'::timestamptz, '2026-08-13 16:00:00-05'::timestamptz, 16, 40, '2026-07-20 10:30:00-05'::timestamptz),
  (12, 12, 2, 18, 3, 1, 'Copa Intercolegiada de Natación', 'Copa Intercolegiada de Natación: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Piscinas Olímpicas Fátima', '2026-12-16 08:00:00-05'::timestamptz, '2026-12-16 16:00:00-05'::timestamptz, 20, 60, '2026-08-21 10:30:00-05'::timestamptz),
  (13, 13, 3, 6, 4, 1, 'Muralismo por la Paz', 'Muralismo por la Paz: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Cra 4 con Calle 9', '2026-10-19 08:00:00-05'::timestamptz, '2026-10-19 16:00:00-05'::timestamptz, 8, 80, '2026-07-22 10:30:00-05'::timestamptz),
  (14, 14, 4, 1, 2, NULL, 'Hackatón Escolar Código Abierto', 'Hackatón Escolar Código Abierto: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Plaza de los Artesanos', '2026-11-22 08:00:00-05'::timestamptz, '2026-11-22 16:00:00-05'::timestamptz, 12, 100, NULL),
  (15, 15, 5, 1, 1, NULL, 'Torneo Nacional de Debate', 'Torneo Nacional de Debate: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Biblioteca Virgilio Barco', '2026-12-25 08:00:00-05'::timestamptz, '2026-12-25 16:00:00-05'::timestamptz, 16, 120, NULL),
  (16, 16, 6, 12, 5, 1, 'Semana del Agua Planeta Azul', 'Semana del Agua Planeta Azul: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Muelle de la Bodeguita', '2026-09-06 08:00:00-05'::timestamptz, '2026-09-06 16:00:00-05'::timestamptz, 20, 40, '2026-08-10 10:30:00-05'::timestamptz),
  (17, 17, 7, 10, 1, NULL, 'Reto Matemático Pitágoras', 'Reto Matemático Pitágoras: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Universidad Industrial de Santander', '2026-11-09 08:00:00-05'::timestamptz, '2026-11-09 16:00:00-05'::timestamptz, 8, 60, NULL),
  (18, 18, 8, 4, 3, 1, 'Taller y Concurso de Poesía Joven', 'Taller y Concurso de Poesía Joven: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Casa de la Literatura', '2026-12-12 08:00:00-05'::timestamptz, '2026-12-12 16:00:00-05'::timestamptz, 12, 80, '2026-08-12 10:30:00-05'::timestamptz),
  (19, 19, 9, 15, 3, 1, 'Expo Emprende Boyacá', 'Expo Emprende Boyacá: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Parque Recreacional del Norte', '2026-10-15 08:00:00-05'::timestamptz, '2026-10-15 16:00:00-05'::timestamptz, 16, 100, '2026-07-13 10:30:00-05'::timestamptz),
  (20, 20, 10, 7, 3, 1, 'Gran Concierto de Orquestas Escolares', 'Gran Concierto de Orquestas Escolares: encuentro para estudiantes de colegios de la region con participacion de varias instituciones.', 'Auditorio Hernando Caicedo', '2026-11-18 08:00:00-05'::timestamptz, '2026-11-18 16:00:00-05'::timestamptz, 20, 120, '2026-08-14 10:30:00-05'::timestamptz)
ON CONFLICT DO NOTHING;

-- 6) ESTUDIANTES (40) Y AUTORIZACIONES DE ACUDIENTES (10) --------------

-- estudiante: 40 registros
INSERT INTO estudiante (id, id_colegio, id_grado, nombre, apellido, documento) VALUES
  (1, 1, 9, 'Mateo', 'Hernández Castro', '1001048271'),
  (2, 1, 10, 'Isabella', 'Rojas Cárdenas', '1001096542'),
  (3, 2, 11, 'Daniel', 'Pardo Gómez', '1001144813'),
  (4, 2, 12, 'Luciana', 'Quintero Vargas', '1001193084'),
  (5, 3, 8, 'Nicolás', 'López Pardo', '1001241355'),
  (6, 3, 1, 'Salomé', 'Vargas Rodríguez', '1001289626'),
  (7, 4, 10, 'Santiago', 'Ortiz Torres', '1001337897'),
  (8, 4, 11, 'Sofía', 'Osorio Suárez', '1001386168'),
  (9, 5, 12, 'Samuel', 'Gómez Salazar', '1001434439'),
  (10, 5, 8, 'Laura', 'Ramírez Ramírez', '1001482710'),
  (11, 6, 9, 'Sebastián', 'Moreno Ortiz', '1001530981'),
  (12, 6, 1, 'Daniela', 'Cárdenas Quintero', '1001579252'),
  (13, 7, 11, 'Tomás', 'Salazar Hernández', '1001627523'),
  (14, 7, 12, 'Valentina', 'García Jiménez', '1001675794'),
  (15, 8, 8, 'Juan David', 'Castro Arango', '1001724065'),
  (16, 8, 9, 'Mariana', 'Suárez García', '1001772336'),
  (17, 9, 10, 'Andrés', 'Arango Moreno', '1001820607'),
  (18, 9, 1, 'Gabriela', 'Martínez Osorio', '1001868878'),
  (19, 10, 12, 'Felipe', 'Torres López', '1001917149'),
  (20, 10, 8, 'Camila', 'Jiménez Rojas', '1001965420'),
  (21, 11, 9, 'Mateo', 'Mejía Mejía', '1002013691'),
  (22, 11, 10, 'Isabella', 'Rodríguez Martínez', '1002061962'),
  (23, 12, 11, 'Daniel', 'Hernández Castro', '1002110233'),
  (24, 12, 1, 'Luciana', 'Rojas Cárdenas', '1002158504'),
  (25, 13, 8, 'Nicolás', 'Pardo Gómez', '1002206775'),
  (26, 13, 9, 'Salomé', 'Quintero Vargas', '1002255046'),
  (27, 14, 10, 'Santiago', 'López Pardo', '1002303317'),
  (28, 14, 11, 'Sofía', 'Vargas Rodríguez', '1002351588'),
  (29, 15, 12, 'Samuel', 'Ortiz Torres', '1002399859'),
  (30, 15, 1, 'Laura', 'Osorio Suárez', '1002448130'),
  (31, 16, 9, 'Sebastián', 'Gómez Salazar', '1002496401'),
  (32, 16, 10, 'Daniela', 'Ramírez Ramírez', '1002544672'),
  (33, 17, 11, 'Tomás', 'Moreno Ortiz', '1002592943'),
  (34, 17, 12, 'Valentina', 'Cárdenas Quintero', '1002641214'),
  (35, 18, 8, 'Juan David', 'Salazar Hernández', '1002689485'),
  (36, 18, 1, 'Mariana', 'García Jiménez', '1002737756'),
  (37, 19, 10, 'Andrés', 'Castro Arango', '1002786027'),
  (38, 19, 11, 'Gabriela', 'Suárez García', '1002834298'),
  (39, 20, 12, 'Felipe', 'Arango Moreno', '1002882569'),
  (40, 20, 8, 'Camila', 'Martínez Osorio', '1002930840')
ON CONFLICT DO NOTHING;

-- autorizacion_acudiente: 10 registros
INSERT INTO autorizacion_acudiente (id, id_estudiante, nombre_acudiente, fecha) VALUES
  (1, 1, 'María Fernanda Pardo', '2026-09-05 09:00:00-05'::timestamptz),
  (2, 2, 'Carlos Eduardo Rojas', '2026-09-06 09:00:00-05'::timestamptz),
  (3, 3, 'Luz Marina Suárez', '2026-09-07 09:00:00-05'::timestamptz),
  (4, 4, 'Jorge Iván Cárdenas', '2026-09-08 09:00:00-05'::timestamptz),
  (5, 5, 'Ana Milena Torres', '2026-09-09 09:00:00-05'::timestamptz),
  (6, 6, 'Hernán Darío Mejía', '2026-09-10 09:00:00-05'::timestamptz),
  (7, 7, 'Claudia Patricia Osorio', '2026-09-11 09:00:00-05'::timestamptz),
  (8, 8, 'Fabio Nelson Vargas', '2026-09-12 09:00:00-05'::timestamptz),
  (9, 9, 'Gloria Esperanza Castro', '2026-09-13 09:00:00-05'::timestamptz),
  (10, 10, 'Luis Alberto Moreno', '2026-09-14 09:00:00-05'::timestamptz)
ON CONFLICT DO NOTHING;

-- 7) INSCRIPCIONES (25) E INSCRIPCIONES DE ESTUDIANTES -----------------

-- inscripcion: 25 registros
INSERT INTO inscripcion (id, id_evento, id_colegio, id_estado) VALUES
  (1, 1, 1, 3),
  (2, 2, 4, 2),
  (3, 3, 7, 2),
  (4, 4, 10, 2),
  (5, 5, 13, 2),
  (6, 6, 16, 1),
  (7, 7, 19, 2),
  (8, 9, 2, 2),
  (9, 11, 5, 2),
  (10, 12, 8, 2),
  (11, 16, 11, 2),
  (12, 18, 14, 2),
  (13, 19, 17, 2),
  (14, 20, 20, 2),
  (15, 1, 3, 2),
  (16, 2, 6, 1),
  (17, 3, 9, 2),
  (18, 4, 12, 2),
  (19, 5, 15, 2),
  (20, 6, 18, 2),
  (21, 7, 1, 2),
  (22, 9, 4, 2),
  (23, 11, 7, 2),
  (24, 12, 10, 2),
  (25, 16, 13, 2)
ON CONFLICT DO NOTHING;

-- inscripcion_estudiante: 44 registros
INSERT INTO inscripcion_estudiante (id, id_inscripcion, id_estudiante, asistio) VALUES
  (1, 2, 7, FALSE),
  (2, 2, 8, FALSE),
  (3, 3, 13, FALSE),
  (4, 3, 14, FALSE),
  (5, 4, 19, FALSE),
  (6, 4, 20, FALSE),
  (7, 5, 25, FALSE),
  (8, 5, 26, FALSE),
  (9, 7, 37, TRUE),
  (10, 7, 38, TRUE),
  (11, 8, 3, FALSE),
  (12, 8, 4, FALSE),
  (13, 9, 9, TRUE),
  (14, 9, 10, TRUE),
  (15, 10, 15, FALSE),
  (16, 10, 16, FALSE),
  (17, 11, 21, TRUE),
  (18, 11, 22, TRUE),
  (19, 12, 27, FALSE),
  (20, 12, 28, FALSE),
  (21, 13, 33, FALSE),
  (22, 13, 34, FALSE),
  (23, 14, 39, FALSE),
  (24, 14, 40, FALSE),
  (25, 15, 5, FALSE),
  (26, 15, 6, FALSE),
  (27, 17, 17, FALSE),
  (28, 17, 18, FALSE),
  (29, 18, 23, FALSE),
  (30, 18, 24, FALSE),
  (31, 19, 29, FALSE),
  (32, 19, 30, FALSE),
  (33, 20, 35, FALSE),
  (34, 20, 36, FALSE),
  (35, 21, 1, TRUE),
  (36, 21, 2, TRUE),
  (37, 22, 7, FALSE),
  (38, 22, 8, FALSE),
  (39, 23, 13, TRUE),
  (40, 23, 14, TRUE),
  (41, 24, 19, FALSE),
  (42, 24, 20, FALSE),
  (43, 25, 25, TRUE),
  (44, 25, 26, TRUE)
ON CONFLICT DO NOTHING;

-- 8) AUDITORIA (10) -----------------------------------------------------

-- auditoria: 10 registros
INSERT INTO auditoria (id, id_usuario, accion, tabla, registro_id, ip) VALUES
  (1, 1, 'login', 'usuario', 1, '190.24.10.20'),
  (2, 1, 'crear_evento', 'evento', 2, '190.24.11.21'),
  (3, 1, 'aprobar_evento', 'evento', 3, '190.24.12.22'),
  (4, 22, 'login', 'usuario', 4, '190.24.13.23'),
  (5, 1, 'crear_estudiante', 'estudiante', 5, '190.24.14.24'),
  (6, 1, 'inscribir_colegio', 'inscripcion', 6, '190.24.15.25'),
  (7, 2, 'login', 'usuario', 7, '190.24.16.26'),
  (8, 13, 'rechazar_evento', 'evento', 8, '190.24.17.27'),
  (9, 2, 'aceptar_inscripcion', 'inscripcion', 9, '190.24.18.28'),
  (10, 1, 'registrar_asistencia', 'inscripcion_estudiante', 10, '190.24.19.29')
ON CONFLICT DO NOTHING;

-- 9) SECUENCIAS: para que los proximos INSERT sigan despues de los datos cargados ------
SELECT setval(pg_get_serial_sequence('rol', 'id'), (SELECT COALESCE(MAX(id), 1) FROM rol));
SELECT setval(pg_get_serial_sequence('modulo', 'id'), (SELECT COALESCE(MAX(id), 1) FROM modulo));
SELECT setval(pg_get_serial_sequence('modulo_por_rol', 'id'), (SELECT COALESCE(MAX(id), 1) FROM modulo_por_rol));
SELECT setval(pg_get_serial_sequence('departamento', 'id'), (SELECT COALESCE(MAX(id), 1) FROM departamento));
SELECT setval(pg_get_serial_sequence('ciudad', 'id'), (SELECT COALESCE(MAX(id), 1) FROM ciudad));
SELECT setval(pg_get_serial_sequence('grado', 'id'), (SELECT COALESCE(MAX(id), 1) FROM grado));
SELECT setval(pg_get_serial_sequence('categoria_evento', 'id'), (SELECT COALESCE(MAX(id), 1) FROM categoria_evento));
SELECT setval(pg_get_serial_sequence('estado_evento', 'id'), (SELECT COALESCE(MAX(id), 1) FROM estado_evento));
SELECT setval(pg_get_serial_sequence('estado_inscripcion', 'id'), (SELECT COALESCE(MAX(id), 1) FROM estado_inscripcion));
SELECT setval(pg_get_serial_sequence('usuario', 'id'), (SELECT COALESCE(MAX(id), 1) FROM usuario));
SELECT setval(pg_get_serial_sequence('organizador', 'id'), (SELECT COALESCE(MAX(id), 1) FROM organizador));
SELECT setval(pg_get_serial_sequence('colegio', 'id'), (SELECT COALESCE(MAX(id), 1) FROM colegio));
SELECT setval(pg_get_serial_sequence('evento', 'id'), (SELECT COALESCE(MAX(id), 1) FROM evento));
SELECT setval(pg_get_serial_sequence('estudiante', 'id'), (SELECT COALESCE(MAX(id), 1) FROM estudiante));
SELECT setval(pg_get_serial_sequence('autorizacion_acudiente', 'id'), (SELECT COALESCE(MAX(id), 1) FROM autorizacion_acudiente));
SELECT setval(pg_get_serial_sequence('inscripcion', 'id'), (SELECT COALESCE(MAX(id), 1) FROM inscripcion));
SELECT setval(pg_get_serial_sequence('inscripcion_estudiante', 'id'), (SELECT COALESCE(MAX(id), 1) FROM inscripcion_estudiante));
SELECT setval(pg_get_serial_sequence('auditoria', 'id'), (SELECT COALESCE(MAX(id), 1) FROM auditoria));

-- Verificacion de cantidades
SELECT 'usuario' t, count(*) FROM usuario UNION ALL SELECT 'organizador', count(*) FROM organizador UNION ALL SELECT 'colegio', count(*) FROM colegio UNION ALL SELECT 'evento', count(*) FROM evento UNION ALL SELECT 'estudiante', count(*) FROM estudiante UNION ALL SELECT 'inscripcion', count(*) FROM inscripcion UNION ALL SELECT 'inscripcion_estudiante', count(*) FROM inscripcion_estudiante;
