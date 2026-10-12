const { Router } = require('express');
const { requireAuth, requireRole } = require('../auth');
const { HttpError, texto, entero, soloCampos, id, q, uno } = require('../util');

const r = Router();
r.use(requireAuth);
const esAdmin = (u) => u.rol === 'administrador';

// Un usuario solo ve sus PQRS; el administrador ve todas. 404 (no 403) si no es suya: no revela que existe.
async function visible(req) {
  const p = await uno('SELECT p.*, t.nombre AS tipo FROM pqrs p JOIN tipo_pqrs t ON t.id = p.id_tipo WHERE p.id = ? AND p.estado = 1', [id(req)]);
  if (!p || (!esAdmin(req.user) && p.id_usuario !== req.user.id)) throw new HttpError(404, 'No encontrado');
  return p;
}

r.post('/', async (req, res) => {
  soloCampos(req.body, ['id_tipo', 'asunto', 'mensaje']);
  const id_tipo = entero(req.body.id_tipo, 'id_tipo');
  const asunto = texto(req.body.asunto, 'asunto', { min: 3, max: 150 });
  const mensaje = texto(req.body.mensaje, 'mensaje', { min: 5, max: 1000 });
  if (!(await uno('SELECT id FROM tipo_pqrs WHERE id = ? AND estado = 1', [id_tipo]))) throw new HttpError(422, 'Tipo de PQRS inválido');
  const radicado = `PQRS-${new Date().getFullYear()}-${Date.now().toString(36).toUpperCase()}`;  // unico
  const ins = await q('INSERT INTO pqrs (radicado, id_tipo, id_usuario, asunto, mensaje) VALUES (?, ?, ?, ?, ?)', [radicado, id_tipo, req.user.id, asunto, mensaje]);
  res.status(201).json(await visible({ params: { id: ins.insertId }, user: req.user }));
});

r.get('/', async (req, res) => {
  const base = 'SELECT p.*, t.nombre AS tipo FROM pqrs p JOIN tipo_pqrs t ON t.id = p.id_tipo WHERE p.estado = 1';
  res.json(esAdmin(req.user)
    ? await q(`${base} ORDER BY p.id DESC LIMIT 500`)
    : await q(`${base} AND p.id_usuario = ? ORDER BY p.id DESC LIMIT 500`, [req.user.id]));
});

r.get('/:id', async (req, res) => res.json(await visible(req)));

r.patch('/:id/responder', requireRole('administrador'), async (req, res) => {
  soloCampos(req.body, ['respuesta']);
  const respuesta = texto(req.body.respuesta, 'respuesta', { min: 3, max: 1000 });
  const p = await visible(req);
  await q('UPDATE pqrs SET respuesta = ?, id_respondio = ?, respondida_en = NOW() WHERE id = ?', [respuesta, req.user.id, p.id]);
  res.json(await visible(req));
});

r.delete('/:id', requireRole('administrador'), async (req, res) => {
  const p = await visible(req);
  await q('UPDATE pqrs SET estado = 0 WHERE id = ?', [p.id]);   // baja logica
  res.status(204).end();
});

module.exports = r;
