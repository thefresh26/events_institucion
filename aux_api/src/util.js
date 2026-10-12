const pool = require('./db');

class HttpError extends Error { constructor(status, detail) { super(detail); this.status = status; } }
const bad = (detail) => new HttpError(422, detail);

// Validadores pequeños (sin librerias): devuelven el valor limpio o lanzan 422.
function texto(v, campo, { min = 1, max = 255, requerido = true } = {}) {
  if (v === undefined || v === null || v === '') { if (requerido) throw bad(`Falta el campo ${campo}`); return null; }
  if (typeof v !== 'string') throw bad(`${campo} debe ser texto`);
  const t = v.trim();
  if (t.length < min || t.length > max) throw bad(`${campo} debe tener entre ${min} y ${max} caracteres`);
  return t;
}
function entero(v, campo, { min = 1, max = 2147483647 } = {}) {
  if (!Number.isInteger(v) || v < min || v > max) throw bad(`${campo} debe ser un entero entre ${min} y ${max}`);
  return v;
}
function soloCampos(body, permitidos) {
  const extra = Object.keys(body || {}).filter((k) => !permitidos.includes(k));
  if (extra.length) throw bad(`Campos no permitidos: ${extra.join(', ')}`);  // p. ej. no se puede mandar "estado" al crear
}
const id = (req) => { const n = Number(req.params.id); if (!Number.isInteger(n) || n < 1) throw bad('id inválido'); return n; };

// Errores de MySQL -> respuestas HTTP claras
function manejarDb(e) {
  if (e.code === 'ER_DUP_ENTRY') throw new HttpError(409, 'Ya existe un registro con ese valor único');
  if (e.code === 'ER_NO_REFERENCED_ROW_2') throw bad('Una referencia no es válida');
  throw e;
}
const q = async (sql, params = []) => { try { return (await pool.execute(sql, params))[0]; } catch (e) { return manejarDb(e); } };
const uno = async (sql, params) => (await q(sql, params))[0];

const slug = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 140);

module.exports = { HttpError, bad, texto, entero, soloCampos, id, q, uno, slug };
