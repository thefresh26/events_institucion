-- Parche: completa 10 registros en rol, estado_evento y estado_inscripcion (se puede ejecutar varias veces)

INSERT INTO rol (id, nombre, descripcion) VALUES
  (1, 'administrador', 'Aprueba eventos y administra organizadores y colegios'),
  (2, 'organizador', 'Crea eventos y gestiona la inscripcion de colegios'),
  (3, 'colegio', 'Inscribe a su institucion y a sus estudiantes en los eventos'),
  (4, 'coordinador', 'Apoya al organizador en la logistica de los eventos'),
  (5, 'docente', 'Acompana a los estudiantes de su colegio durante el evento'),
  (6, 'acudiente', 'Autoriza la participacion de sus acudidos'),
  (7, 'jurado', 'Evalua las presentaciones del evento'),
  (8, 'auditor', 'Consulta registros y reportes sin modificarlos'),
  (9, 'soporte', 'Atiende solicitudes y problemas de los usuarios'),
  (10, 'invitado', 'Consulta eventos publicados sin inscribirse')
ON CONFLICT DO NOTHING;

INSERT INTO estado_evento (id, nombre) VALUES
  (1, 'borrador'),
  (2, 'pendiente'),
  (3, 'publicado'),
  (4, 'rechazado'),
  (5, 'cerrado'),
  (6, 'en_revision'),
  (7, 'cancelado'),
  (8, 'aplazado'),
  (9, 'finalizado'),
  (10, 'archivado')
ON CONFLICT DO NOTHING;

INSERT INTO estado_inscripcion (id, nombre) VALUES
  (1, 'pendiente'),
  (2, 'aceptada'),
  (3, 'rechazada'),
  (4, 'en_lista_espera'),
  (5, 'cancelada'),
  (6, 'vencida'),
  (7, 'confirmada'),
  (8, 'en_revision'),
  (9, 'sin_cupo'),
  (10, 'retirada')
ON CONFLICT DO NOTHING;

SELECT setval(pg_get_serial_sequence('rol','id'),(SELECT MAX(id) FROM rol));
SELECT setval(pg_get_serial_sequence('estado_evento','id'),(SELECT MAX(id) FROM estado_evento));
SELECT setval(pg_get_serial_sequence('estado_inscripcion','id'),(SELECT MAX(id) FROM estado_inscripcion));
