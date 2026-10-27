-- ============================================================================
-- Conexion Escolar - valores por defecto que antes ponia el ORM desde Python.
-- Deja la base de Neon igual a scripts/schema.sql.
--
-- Es SEGURO y REPETIBLE: SET DEFAULT solo cambia el valor que se usa cuando un INSERT
-- no envia la columna. No modifica ni borra filas existentes y se puede ejecutar varias veces.
-- Uso: pegar completo en el SQL Editor de Neon.
-- ============================================================================
BEGIN;

ALTER TABLE usuario                ALTER COLUMN activo  SET DEFAULT true;
ALTER TABLE autorizacion_acudiente ALTER COLUMN vigente SET DEFAULT true;
ALTER TABLE inscripcion_estudiante ALTER COLUMN asistio SET DEFAULT false;

COMMIT;
