-- ============================================================================
-- Conexion Escolar - script_mysql.sql (API auxiliar Express + MySQL)
-- Crea la base, las 4 tablas (con estado, creado y actualizado) y datos de ejemplo realistas:
-- 20 pqrs, 20 comunicados, 20 valoraciones y 10 tipos de pqrs. Se puede ejecutar varias veces.
-- Uso:  mysql -u root -p < script_mysql.sql
-- ============================================================================
CREATE DATABASE IF NOT EXISTS conexion_escolar_aux CHARACTER SET utf8mb4;
USE conexion_escolar_aux;

-- ============================================================================
-- Parcial I - Base de datos AUXILIAR (MySQL) de Conexión Escolar
-- La API principal (FastAPI + PostgreSQL) maneja eventos/colegios/inscripciones.
-- Esta base auxiliar guarda lo que NO es transaccional del negocio:
--   PQRS (peticiones, quejas, reclamos y sugerencias), comunicados y valoraciones de eventos.
-- Todas las tablas: llave primaria, campos unicos, estado, creado y actualizado.
--   estado      TINYINT(1) NOT NULL DEFAULT 1   (0 = eliminado; el registro NO se borra)
--   creado      TIMESTAMP  DEFAULT CURRENT_TIMESTAMP
--   actualizado TIMESTAMP  DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP  (lo maneja MySQL)
-- id_usuario / id_evento / id_autor son ids de la base principal (PostgreSQL); no hay FK entre motores distintos.
-- ============================================================================
CREATE TABLE IF NOT EXISTS tipo_pqrs (
  id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nombre      VARCHAR(50)  NOT NULL,
  descripcion VARCHAR(255) NULL,
  estado      TINYINT(1)   NOT NULL DEFAULT 1,
  creado      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_tipo_pqrs_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS pqrs (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  radicado      VARCHAR(30)  NOT NULL,
  id_tipo       INT UNSIGNED NOT NULL,
  id_usuario    INT UNSIGNED NOT NULL,
  asunto        VARCHAR(150) NOT NULL,
  mensaje       VARCHAR(1000) NOT NULL,
  respuesta     VARCHAR(1000) NULL,
  id_respondio  INT UNSIGNED NULL,
  respondida_en TIMESTAMP    NULL,
  estado        TINYINT(1)   NOT NULL DEFAULT 1,
  creado        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_pqrs_radicado (radicado),
  KEY ix_pqrs_usuario (id_usuario),
  CONSTRAINT fk_pqrs_tipo FOREIGN KEY (id_tipo) REFERENCES tipo_pqrs (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS comunicado (
  id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  slug        VARCHAR(160) NOT NULL,
  titulo      VARCHAR(150) NOT NULL,
  contenido   VARCHAR(2000) NOT NULL,
  dirigido_a  ENUM('todos','organizador','colegio') NOT NULL DEFAULT 'todos',
  id_autor    INT UNSIGNED NOT NULL,
  estado      TINYINT(1)   NOT NULL DEFAULT 1,
  creado      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_comunicado_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS valoracion_evento (
  id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_evento   INT UNSIGNED NOT NULL,
  id_usuario  INT UNSIGNED NOT NULL,
  puntuacion  TINYINT UNSIGNED NOT NULL,
  comentario  VARCHAR(500) NULL,
  estado      TINYINT(1)   NOT NULL DEFAULT 1,
  creado      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_valoracion_evento_usuario (id_evento, id_usuario),
  CONSTRAINT ck_puntuacion CHECK (puntuacion BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- DATOS ----------------------------------------------------------------

-- tipo_pqrs: 10 registros
INSERT IGNORE INTO tipo_pqrs (id, nombre, descripcion) VALUES
  (1, 'Petición', 'Solicitud de información o de un servicio'),
  (2, 'Queja', 'Inconformidad con el trato o el servicio recibido'),
  (3, 'Reclamo', 'Reclamación por un derecho no atendido'),
  (4, 'Sugerencia', 'Propuesta para mejorar la plataforma'),
  (5, 'Felicitación', 'Reconocimiento a un servicio o evento'),
  (6, 'Consulta', 'Duda sobre el uso de la plataforma'),
  (7, 'Denuncia', 'Reporte de una conducta indebida'),
  (8, 'Certificado', 'Solicitud de constancia de participación'),
  (9, 'Soporte técnico', 'Falla o error en la plataforma'),
  (10, 'Corrección de datos', 'Solicitud de modificar datos registrados');

-- pqrs: 20 registros
INSERT IGNORE INTO pqrs (id, radicado, id_tipo, id_usuario, asunto, mensaje, respuesta, id_respondio, respondida_en, creado) VALUES
  (1, 'PQRS-2026-0001', 1, 22, 'Consulta sobre cupos del evento', 'Buenos días, quisiera saber si aún hay cupos disponibles para nuestro colegio en el evento al que nos inscribimos.', NULL, NULL, NULL, '2026-09-01 08:15:00'),
  (2, 'PQRS-2026-0002', 8, 25, 'Certificado de participación', 'Solicito la constancia de participación de nuestros estudiantes en la Olimpiada Regional de Matemáticas.', 'Gracias por escribirnos. Revisamos su caso y ya fue atendido; quedamos atentos a cualquier novedad.', 1, '2026-09-02 14:30:00', '2026-09-02 08:15:00'),
  (3, 'PQRS-2026-0003', 5, 28, 'Felicitaciones por la organización', 'Queremos felicitar al equipo organizador por la logística del evento; todo transcurrió sin contratiempos.', 'Gracias por escribirnos. Revisamos su caso y ya fue atendido; quedamos atentos a cualquier novedad.', 1, '2026-09-03 14:30:00', '2026-09-03 08:15:00'),
  (4, 'PQRS-2026-0004', 9, 31, 'No puedo cargar estudiantes', 'Al intentar registrar un estudiante la página muestra un error. Agradezco revisar.', NULL, NULL, NULL, '2026-09-04 08:15:00'),
  (5, 'PQRS-2026-0005', 2, 34, 'Demora en la respuesta de inscripción', 'Hace dos semanas enviamos la solicitud y aún aparece como pendiente.', 'Gracias por escribirnos. Revisamos su caso y ya fue atendido; quedamos atentos a cualquier novedad.', 1, '2026-09-05 14:30:00', '2026-09-05 08:15:00'),
  (6, 'PQRS-2026-0006', 10, 37, 'Dato incorrecto en el NIT', 'El NIT de nuestra institución aparece con un dígito de verificación errado.', 'Gracias por escribirnos. Revisamos su caso y ya fue atendido; quedamos atentos a cualquier novedad.', 1, '2026-09-06 14:30:00', '2026-09-06 08:15:00'),
  (7, 'PQRS-2026-0007', 4, 40, 'Sugerencia: filtro por ciudad', 'Sería útil poder filtrar los eventos por ciudad y por categoría desde el inicio.', NULL, NULL, NULL, '2026-09-07 08:15:00'),
  (8, 'PQRS-2026-0008', 3, 23, 'Reclamo por cupo asignado', 'Se aceptó nuestra inscripción pero el cupo de estudiantes quedó menor al solicitado.', 'Gracias por escribirnos. Revisamos su caso y ya fue atendido; quedamos atentos a cualquier novedad.', 1, '2026-09-08 14:30:00', '2026-09-08 08:15:00'),
  (9, 'PQRS-2026-0009', 6, 26, 'Pregunta sobre autorización de acudientes', '¿Dónde se carga la autorización firmada de los acudientes?', 'Gracias por escribirnos. Revisamos su caso y ya fue atendido; quedamos atentos a cualquier novedad.', 1, '2026-09-09 14:30:00', '2026-09-09 08:15:00'),
  (10, 'PQRS-2026-0010', 7, 29, 'Reporte de comportamiento', 'Durante el evento se presentó un inconveniente de seguridad en el ingreso.', NULL, NULL, NULL, '2026-09-10 08:15:00'),
  (11, 'PQRS-2026-0011', 1, 32, 'Consulta sobre cupos del evento (seguimiento)', 'Buenos días, quisiera saber si aún hay cupos disponibles para nuestro colegio en el evento al que nos inscribimos.', 'Gracias por escribirnos. Revisamos su caso y ya fue atendido; quedamos atentos a cualquier novedad.', 1, '2026-09-11 14:30:00', '2026-09-11 08:15:00'),
  (12, 'PQRS-2026-0012', 8, 35, 'Certificado de participación (seguimiento)', 'Solicito la constancia de participación de nuestros estudiantes en la Olimpiada Regional de Matemáticas.', 'Gracias por escribirnos. Revisamos su caso y ya fue atendido; quedamos atentos a cualquier novedad.', 1, '2026-09-12 14:30:00', '2026-09-12 08:15:00'),
  (13, 'PQRS-2026-0013', 5, 38, 'Felicitaciones por la organización (seguimiento)', 'Queremos felicitar al equipo organizador por la logística del evento; todo transcurrió sin contratiempos.', NULL, NULL, NULL, '2026-09-13 08:15:00'),
  (14, 'PQRS-2026-0014', 9, 41, 'No puedo cargar estudiantes (seguimiento)', 'Al intentar registrar un estudiante la página muestra un error. Agradezco revisar.', 'Gracias por escribirnos. Revisamos su caso y ya fue atendido; quedamos atentos a cualquier novedad.', 1, '2026-09-14 14:30:00', '2026-09-14 08:15:00'),
  (15, 'PQRS-2026-0015', 2, 24, 'Demora en la respuesta de inscripción (seguimiento)', 'Hace dos semanas enviamos la solicitud y aún aparece como pendiente.', 'Gracias por escribirnos. Revisamos su caso y ya fue atendido; quedamos atentos a cualquier novedad.', 1, '2026-09-15 14:30:00', '2026-09-15 08:15:00'),
  (16, 'PQRS-2026-0016', 10, 27, 'Dato incorrecto en el NIT (seguimiento)', 'El NIT de nuestra institución aparece con un dígito de verificación errado.', NULL, NULL, NULL, '2026-09-16 08:15:00'),
  (17, 'PQRS-2026-0017', 4, 30, 'Sugerencia: filtro por ciudad (seguimiento)', 'Sería útil poder filtrar los eventos por ciudad y por categoría desde el inicio.', 'Gracias por escribirnos. Revisamos su caso y ya fue atendido; quedamos atentos a cualquier novedad.', 1, '2026-09-17 14:30:00', '2026-09-17 08:15:00'),
  (18, 'PQRS-2026-0018', 3, 33, 'Reclamo por cupo asignado (seguimiento)', 'Se aceptó nuestra inscripción pero el cupo de estudiantes quedó menor al solicitado.', 'Gracias por escribirnos. Revisamos su caso y ya fue atendido; quedamos atentos a cualquier novedad.', 1, '2026-09-18 14:30:00', '2026-09-18 08:15:00'),
  (19, 'PQRS-2026-0019', 6, 36, 'Pregunta sobre autorización de acudientes (seguimiento)', '¿Dónde se carga la autorización firmada de los acudientes?', NULL, NULL, NULL, '2026-09-19 08:15:00'),
  (20, 'PQRS-2026-0020', 7, 39, 'Reporte de comportamiento (seguimiento)', 'Durante el evento se presentó un inconveniente de seguridad en el ingreso.', 'Gracias por escribirnos. Revisamos su caso y ya fue atendido; quedamos atentos a cualquier novedad.', 1, '2026-09-20 14:30:00', '2026-09-20 08:15:00');

-- comunicado: 20 registros
INSERT IGNORE INTO comunicado (id, slug, titulo, contenido, dirigido_a, id_autor) VALUES
  (1, 'inicio-de-inscripciones-2026', 'Inician las inscripciones a eventos 2026', 'Los colegios ya pueden inscribirse a los eventos publicados. Revisen cupos y fechas.', 'colegio', 1),
  (2, 'nuevo-modulo-de-asistencia', 'Nuevo módulo de asistencia', 'Los organizadores pueden registrar la asistencia de los estudiantes desde el módulo de asistencia.', 'organizador', 1),
  (3, 'mantenimiento-programado-octubre', 'Mantenimiento programado', 'La plataforma estará en mantenimiento el sábado de 2:00 a 4:00 a. m.', 'todos', 1),
  (4, 'recomendaciones-de-seguridad', 'Recomendaciones de seguridad', 'No comparta su contraseña y cierre la sesión al terminar de usar la plataforma.', 'todos', 1),
  (5, 'autorizacion-de-acudientes', 'Autorización de acudientes obligatoria', 'Todo estudiante debe tener la autorización de su acudiente antes del evento.', 'colegio', 1),
  (6, 'plazo-para-aprobar-eventos', 'Plazo para aprobar eventos', 'Los eventos pendientes se revisan en un máximo de cinco días hábiles.', 'organizador', 1),
  (7, 'feria-nacional-de-ciencias', 'Feria Nacional de Ciencias 2026', 'Última semana para inscribir estudiantes a la Feria Nacional de Ciencias.', 'colegio', 1),
  (8, 'encuesta-de-satisfaccion', 'Encuesta de satisfacción', 'Califique los eventos a los que asistió; su opinión mejora la plataforma.', 'todos', 1),
  (9, 'cierre-de-eventos-del-semestre', 'Cierre de eventos del semestre', 'Los organizadores deben cerrar los eventos finalizados para generar reportes.', 'organizador', 1),
  (10, 'actualizacion-de-datos', 'Actualización de datos institucionales', 'Verifique que NIT, dirección y teléfono de su colegio estén al día.', 'colegio', 1),
  (11, 'inicio-de-inscripciones-2026-2', 'Inician las inscripciones a eventos 2026 (recordatorio)', 'Los colegios ya pueden inscribirse a los eventos publicados. Revisen cupos y fechas.', 'colegio', 1),
  (12, 'nuevo-modulo-de-asistencia-2', 'Nuevo módulo de asistencia (recordatorio)', 'Los organizadores pueden registrar la asistencia de los estudiantes desde el módulo de asistencia.', 'organizador', 1),
  (13, 'mantenimiento-programado-octubre-2', 'Mantenimiento programado (recordatorio)', 'La plataforma estará en mantenimiento el sábado de 2:00 a 4:00 a. m.', 'todos', 1),
  (14, 'recomendaciones-de-seguridad-2', 'Recomendaciones de seguridad (recordatorio)', 'No comparta su contraseña y cierre la sesión al terminar de usar la plataforma.', 'todos', 1),
  (15, 'autorizacion-de-acudientes-2', 'Autorización de acudientes obligatoria (recordatorio)', 'Todo estudiante debe tener la autorización de su acudiente antes del evento.', 'colegio', 1),
  (16, 'plazo-para-aprobar-eventos-2', 'Plazo para aprobar eventos (recordatorio)', 'Los eventos pendientes se revisan en un máximo de cinco días hábiles.', 'organizador', 1),
  (17, 'feria-nacional-de-ciencias-2', 'Feria Nacional de Ciencias 2026 (recordatorio)', 'Última semana para inscribir estudiantes a la Feria Nacional de Ciencias.', 'colegio', 1),
  (18, 'encuesta-de-satisfaccion-2', 'Encuesta de satisfacción (recordatorio)', 'Califique los eventos a los que asistió; su opinión mejora la plataforma.', 'todos', 1),
  (19, 'cierre-de-eventos-del-semestre-2', 'Cierre de eventos del semestre (recordatorio)', 'Los organizadores deben cerrar los eventos finalizados para generar reportes.', 'organizador', 1),
  (20, 'actualizacion-de-datos-2', 'Actualización de datos institucionales (recordatorio)', 'Verifique que NIT, dirección y teléfono de su colegio estén al día.', 'colegio', 1);

-- valoracion_evento: 20 registros
INSERT IGNORE INTO valoracion_evento (id, id_evento, id_usuario, puntuacion, comentario) VALUES
  (1, 1, 22, 3, 'Excelente organización y muy buena logística.'),
  (2, 2, 29, 4, 'Los estudiantes aprendieron mucho, volveremos el próximo año.'),
  (3, 3, 36, 5, 'Buen evento, aunque el sonido del auditorio falló un rato.'),
  (4, 4, 23, 3, 'Muy bien, pero faltó señalización para llegar.'),
  (5, 5, 30, 4, 'Una experiencia motivadora para nuestros jóvenes.'),
  (6, 12, 37, 5, 'Cumplió las expectativas.'),
  (7, 7, 24, 3, NULL),
  (8, 1, 31, 4, 'Los tiempos se alargaron más de lo previsto.'),
  (9, 2, 38, 5, 'Gran nivel de los participantes.'),
  (10, 3, 25, 3, 'Recomendado para todos los colegios.'),
  (11, 4, 32, 4, 'Excelente organización y muy buena logística.'),
  (12, 5, 39, 5, 'Los estudiantes aprendieron mucho, volveremos el próximo año.'),
  (13, 12, 26, 3, 'Buen evento, aunque el sonido del auditorio falló un rato.'),
  (14, 7, 33, 4, 'Muy bien, pero faltó señalización para llegar.'),
  (15, 1, 40, 5, 'Una experiencia motivadora para nuestros jóvenes.'),
  (16, 2, 27, 3, 'Cumplió las expectativas.'),
  (17, 3, 34, 4, NULL),
  (18, 4, 41, 5, 'Los tiempos se alargaron más de lo previsto.'),
  (19, 5, 28, 3, 'Gran nivel de los participantes.'),
  (20, 12, 35, 4, 'Recomendado para todos los colegios.');

SELECT 'tipo_pqrs' t, COUNT(*) n FROM tipo_pqrs UNION ALL SELECT 'pqrs', COUNT(*) FROM pqrs UNION ALL SELECT 'comunicado', COUNT(*) FROM comunicado UNION ALL SELECT 'valoracion_evento', COUNT(*) FROM valoracion_evento;
