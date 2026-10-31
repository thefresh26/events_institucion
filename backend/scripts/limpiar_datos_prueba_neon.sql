-- Borra SOLO los datos de prueba de Neon (usuarios 2, 3 y 4 y todo lo que cuelga de ellos).
-- CONSERVA al administrador del sistema (id 1, admin@admin.com), los catalogos, roles y modulos.
-- Ejecutar ANTES de cargar los datos nuevos de script_neon.sql.
BEGIN;
DELETE FROM inscripcion_estudiante;
DELETE FROM inscripcion;
DELETE FROM autorizacion_acudiente;
DELETE FROM estudiante;
DELETE FROM evento;
DELETE FROM colegio;
DELETE FROM organizador;
DELETE FROM auditoria WHERE id_usuario IS DISTINCT FROM 1;
DELETE FROM usuario WHERE id <> 1;
COMMIT;
SELECT 'usuario' t, count(*) FROM usuario UNION ALL SELECT 'evento', count(*) FROM evento UNION ALL SELECT 'colegio', count(*) FROM colegio;
