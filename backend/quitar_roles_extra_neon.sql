-- Deja solo los 3 roles del sistema (administrador, organizador, colegio). Se puede ejecutar varias veces.
DELETE FROM modulo_por_rol WHERE id_rol > 3;
DELETE FROM rol WHERE id > 3;
SELECT setval(pg_get_serial_sequence('rol','id'),(SELECT MAX(id) FROM rol));
SELECT id, nombre FROM rol ORDER BY id;
