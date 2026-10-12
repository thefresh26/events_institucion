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

INSERT IGNORE INTO tipo_pqrs (nombre, descripcion) VALUES
  ('Petición',   'Solicitud de información o de un servicio'),
  ('Queja',      'Inconformidad con el trato o el servicio recibido'),
  ('Reclamo',    'Reclamación por un derecho no atendido'),
  ('Sugerencia', 'Propuesta para mejorar la plataforma');
