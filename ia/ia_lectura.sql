-- ============================================================================
-- Conexion Escolar - usuario de SOLO LECTURA para las practicas de IA (text_to_sql y groq_mcp).
-- NO se ejecuta automaticamente. Uso: pegar completo en el SQL Editor de Neon, reemplazando antes
-- <clave-larga-para-ia_lectura> por una clave larga (que NO se guarda en el repositorio).
-- Si tu base no se llama neondb, cambia ese nombre en GRANT CONNECT.
-- Es repetible: se puede ejecutar varias veces.
--
-- Lo que ia_lectura NO puede ver:
--   * la tabla usuario (correos y la columna contrasena)
--   * la tabla auditoria (guarda direcciones IP)
--   * estudiante.documento en claro (solo enmascarado, en la vista estudiante_enmascarado)
--   * autorizacion_acudiente.nombre_acudiente
-- Y no puede escribir nada: la sesion es de solo lectura y cada consulta tiene limite de 5 s.
-- ============================================================================
BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ia_lectura') THEN
    CREATE ROLE ia_lectura LOGIN PASSWORD '<clave-larga-para-ia_lectura>';
  END IF;
END $$;

ALTER ROLE ia_lectura SET default_transaction_read_only = on;
ALTER ROLE ia_lectura SET statement_timeout = '5s';

GRANT CONNECT ON DATABASE neondb TO ia_lectura;
GRANT USAGE ON SCHEMA public TO ia_lectura;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM ia_lectura;   -- se parte de cero y se da solo lo necesario

-- Tablas completas (no tienen datos personales sensibles)
GRANT SELECT ON rol, modulo, modulo_por_rol, departamento, ciudad, grado, categoria_evento, estado_evento,
                estado_inscripcion, organizador, colegio, evento, inscripcion, inscripcion_estudiante
TO ia_lectura;

-- Tablas con columnas sensibles: solo algunas columnas
GRANT SELECT (id, id_colegio, id_grado, nombre, apellido, estado, creado, actualizado) ON estudiante TO ia_lectura;
GRANT SELECT (id, id_estudiante, fecha, vigente, estado, creado, actualizado) ON autorizacion_acudiente TO ia_lectura;

-- Documento del estudiante enmascarado (ej. 109*****21); la vista se ejecuta con los permisos de su dueño
CREATE OR REPLACE VIEW estudiante_enmascarado AS
SELECT id, id_colegio, id_grado, nombre, apellido,
       left(documento, 3) || repeat('*', greatest(length(documento) - 5, 0)) || right(documento, 2) AS documento,
       estado
FROM estudiante;
GRANT SELECT ON estudiante_enmascarado TO ia_lectura;

COMMIT;
