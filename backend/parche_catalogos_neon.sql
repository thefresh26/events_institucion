-- Parche: completa 10 registros en estado_evento y estado_inscripcion (se puede ejecutar varias veces)

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

SELECT setval(pg_get_serial_sequence('estado_evento','id'),(SELECT MAX(id) FROM estado_evento));
SELECT setval(pg_get_serial_sequence('estado_inscripcion','id'),(SELECT MAX(id) FROM estado_inscripcion));
