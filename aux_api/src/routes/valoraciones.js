const { Router } = require('express');
const { requireAuth, requireRole } = require('../auth');
const { HttpError, texto, entero, soloCampos, id, q, uno } = require('../util');

const r = Router();
r.use(requireAuth);

// Un colegio califica un evento (1 a 5). Una sola valoracion por colegio y evento (campo unico compuesto).
r.post('/', requireRole('colegio'), async (req, res) => {
  soloCampos(req.body, ['id_evento', 'puntuacion', 'comentario']);
  const id_evento = entero(req.body.id_evento, 'id_evento');
  const puntuacion = entero(req.body.puntuacion, 'puntuacion', { min: 1, max: 5 });
  const comentario = texto(req.body.comentario, 'comentario', { max: 500, requerido: false });
  const ins = await q('INSERT INTO valoracion_evento (id_evento, id_usuario, puntuacion, comentario) VALUES (?, ?, ?, ?)',
    [id_evento, req.user.id, puntuacion, comentario]);
  res.status(201).json(await uno('SELECT * FROM valoracion_evento WHERE id = ?', [ins.insertId]));
});

// Valoraciones de un evento + promedio
r.get('/evento/:id', async (req, res) => {
  const n = id(req);
  const lista = await q('SELECT id, id_evento, puntuacion, comentario, creado FROM valoracion_evento WHERE id_evento = ? AND estado = 1 ORDER BY id DESC LIMIT 500', [n]);
  const promedio = lista.length ? Math.round((lista.reduce((s, v) => s + v.puntuacion, 0) / lista.length) * 10) / 10 : null;
  res.json({ id_evento: n, total: lista.length, promedio, valoraciones: lista });
});

// El dueño o el administrador la eliminan (baja logica)
r.delete('/:id', async (req, res) => {
  const v = await uno('SELECT * FROM valoracion_evento WHERE id = ? AND estado = 1', [id(req)]);
  if (!v || (req.user.rol !== 'administrador' && v.id_usuario !== req.user.id)) throw new HttpError(404, 'No encontrado');
  await q('UPDATE valoracion_evento SET estado = 0 WHERE id = ?', [v.id]);
  res.status(204).end();
});

module.exports = r;
