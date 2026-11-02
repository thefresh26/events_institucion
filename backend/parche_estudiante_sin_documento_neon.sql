-- Parche: el estudiante ya no se identifica por documento (ningun formulario pide cedula ni ID).
-- Se identifica por nombre, apellido y grado dentro de su colegio. Se puede ejecutar varias veces.
ALTER TABLE estudiante ALTER COLUMN documento DROP NOT NULL;
ALTER TABLE estudiante DROP CONSTRAINT IF EXISTS estudiante_id_colegio_documento_key;
CREATE UNIQUE INDEX IF NOT EXISTS uq_estudiante_nombre_grado ON estudiante (id_colegio, lower(nombre), lower(apellido), id_grado) WHERE estado = true;
