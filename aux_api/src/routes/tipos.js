const { Router } = require('express');
const { requireAuth, requireRole } = require('../auth');
const { HttpError, texto, soloCampos, id, q, uno } = require('../util');

const r = Router();
const admin = requireRole('administrador');
const buscar = async (n) => { const t = await uno('SELECT * FROM tipo_pqrs WHERE id = ?', [n]); if (!t) throw new HttpError(404, 'No encontrado'); return t; };

// Cualquier usuario autenticado ve los tipos activos (estado = 1)
r.get('/', requireAuth, async (_req, res) => res.json(await q('SELECT * FROM tipo_pqrs WHERE estado = 1 ORDER BY id')));

r.post('/', requireAuth, admin, async (req, res) => {
  soloCampos(req.body, ['nombre', 'descripcion']);
  const nombre = texto(req.body.nombre, 'nombre', { max: 50 });
  const descripcion = texto(req.body.descripcion, 'descripcion', { requerido: false });
  const ins = await q('INSERT INTO tipo_pqrs (nombre, descripcion) VALUES (?, ?)', [nombre, descripcion]);
  res.status(201).json(await buscar(ins.insertId));
});

r.put('/:id', requireAuth, admin, async (req, res) => {
  soloCampos(req.body, ['nombre', 'descripcion']);
  const n = id(req); const t = await buscar(n);
  const nombre = req.body.nombre === undefined ? t.nombre : texto(req.body.nombre, 'nombre', { max: 50 });
  const descripcion = req.body.descripcion === undefined ? t.descripcion : texto(req.body.descripcion, 'descripcion', { requerido: false });
  await q('UPDATE tipo_pqrs SET nombre = ?, descripcion = ? WHERE id = ?', [nombre, descripcion, n]);
  res.json(await buscar(n));
});

// Baja logica: estado = 0. La fila NO se borra.
r.delete('/:id', requireAuth, admin, async (req, res) => {
  const n = id(req); await buscar(n);
  await q('UPDATE tipo_pqrs SET estado = 0 WHERE id = ?', [n]);
  res.json(await buscar(n));
});

// Manipular el campo estado a mano (0 = eliminado, 1 = restaurar)
r.patch('/:id/estado', requireAuth, admin, async (req, res) => {
  soloCampos(req.body, ['estado']);
  if (typeof req.body.estado !== 'boolean') throw new HttpError(422, 'estado debe ser true o false');
  const n = id(req); await buscar(n);
  await q('UPDATE tipo_pqrs SET estado = ? WHERE id = ?', [req.body.estado ? 1 : 0, n]);
  res.json(await buscar(n));
});

module.exports = r;
