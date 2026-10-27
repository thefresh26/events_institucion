-- ============================================================================
-- Parcial I - Conexion Escolar (PostgreSQL / Neon)
-- Agrega a las 18 tablas los 3 campos de auditoria que pide el taller:
--   estado      boolean  NOT NULL DEFAULT true   (false = eliminado; el registro NO se borra)
--   creado      timestamptz NOT NULL DEFAULT now()  (no cambia)
--   actualizado timestamptz NOT NULL DEFAULT now()  (un TRIGGER lo refresca en cada UPDATE)
-- Es IDEMPOTENTE: se puede ejecutar varias veces sin dañar nada. Pegar completo en el SQL Editor de Neon.
-- ============================================================================
BEGIN;

-- 1) Columnas que ya existian con otro nombre -> se renombran (se conservan los datos).
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='usuario' AND column_name='creado_en') THEN
    ALTER TABLE usuario RENAME COLUMN creado_en TO creado; END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='evento' AND column_name='creado_en') THEN
    ALTER TABLE evento RENAME COLUMN creado_en TO creado; END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='inscripcion' AND column_name='creada_en') THEN
    ALTER TABLE inscripcion RENAME COLUMN creada_en TO creado; END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='auditoria' AND column_name='creada_en') THEN
    ALTER TABLE auditoria RENAME COLUMN creada_en TO creado; END IF;
  -- estudiante.activo era justamente un "estado": pasa a llamarse estado
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='estudiante' AND column_name='activo')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='estudiante' AND column_name='estado') THEN
    ALTER TABLE estudiante RENAME COLUMN activo TO estado; END IF;
END $$;

-- 2) Funcion del trigger: pone actualizado = now() cada vez que se modifica una fila.
CREATE OR REPLACE FUNCTION set_actualizado() RETURNS trigger AS $$
BEGIN
  NEW.actualizado = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3) Las 3 columnas + el trigger en las 18 tablas.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['rol','modulo','modulo_por_rol','usuario','departamento','ciudad','colegio','organizador',
                           'grado','estudiante','autorizacion_acudiente','categoria_evento','estado_evento','evento',
                           'estado_inscripcion','inscripcion','inscripcion_estudiante','auditoria']
  LOOP
    EXECUTE format('ALTER TABLE %I ADD COLUMN IF NOT EXISTS estado boolean NOT NULL DEFAULT true', t);
    EXECUTE format('ALTER TABLE %I ADD COLUMN IF NOT EXISTS creado timestamptz NOT NULL DEFAULT now()', t);
    EXECUTE format('ALTER TABLE %I ADD COLUMN IF NOT EXISTS actualizado timestamptz NOT NULL DEFAULT now()', t);
    EXECUTE format('DROP TRIGGER IF EXISTS trg_actualizado ON %I', t);
    EXECUTE format('CREATE TRIGGER trg_actualizado BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION set_actualizado()', t);
  END LOOP;
END $$;

-- 4) Campo unico: una autorizacion de acudiente por estudiante.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_autorizacion_estudiante') THEN
    ALTER TABLE autorizacion_acudiente ADD CONSTRAINT uq_autorizacion_estudiante UNIQUE (id_estudiante);
  END IF;
END $$;

COMMIT;

-- Verificacion: debe devolver 18 filas con las 3 columnas (3 columnas x 18 tablas = 54).
SELECT table_name,
       bool_or(column_name = 'estado') AS estado,
       bool_or(column_name = 'creado') AS creado,
       bool_or(column_name = 'actualizado') AS actualizado
FROM information_schema.columns
WHERE table_schema = 'public' AND column_name IN ('estado','creado','actualizado')
GROUP BY table_name ORDER BY table_name;
