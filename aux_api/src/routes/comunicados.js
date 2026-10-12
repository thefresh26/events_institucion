const { Router } = require('express');
const { requireAuth, requireRole } = require('../auth');
const { HttpError, texto, soloCampos, id, q, uno, slug } = require('../util');

const r = Router();
r.use(requireAuth);
const admin = requireRole('administrador');
const DEST = ['todos', 'organizador', 'colegio'];
const buscar = async (n) => { const c = await uno('SELECT * FROM comunicado WHERE id = ?', [n]); if (!c) throw new HttpError(404, 'No encontrado'); return c; };
const destino = (v) => { if (v !== undefined && !DEST.includes(v)) throw new HttpError(422, `dirigido_a debe ser: ${DEST.join(', ')}`); return v || 'todos'; };

// Cada usuario ve los comunicados para "todos" y los de su rol; el administrador ve todos los activos.
r.get('/', async (req, res) => {
  const base = 'SELECT * FROM comunicado WHERE estado = 1';
  res.json(req.user.rol === 'administrador'
    ? await q(`${base} ORDER BY id DESC LIMIT 200`)
    : await q(`${base} AND dirigido_a IN ('todos', ?) ORDER BY id DESC LIMIT 200`, [req.user.rol]));
});

r.post('/', admin, async (req, res) => {
  soloCampos(req.body, ['titulo', 'contenido', 'dirigido_a']);
  const titulo = texto(req.body.titulo, 'titulo', { min: 3, max: 150 });
  const contenido = texto(req.body.contenido, 'contenido', { min: 5, max: 2000 });
  const ins = await q('INSERT INTO comunicado (slug, titulo, contenido, dirigido_a, id_autor) VALUES (?, ?, ?, ?, ?)',
    [slug(titulo), titulo, contenido, destino(req.body.dirigido_a), req.user.id]);   // slug unico: mismo titulo = 409
  res.status(201).json(await buscar(ins.insertId));
});

r.put('/:id', admin, async (req, res) => {
  soloCampos(req.body, ['titulo', 'contenido', 'dirigido_a']);
  const c = await buscar(id(req));
  const titulo = req.body.titulo === undefined ? c.titulo : texto(req.body.titulo, 'titulo', { min: 3, max: 150 });
  const contenido = req.body.contenido === undefined ? c.contenido : texto(req.body.contenido, 'contenido', { min: 5, max: 2000 });
  await q('UPDATE comunicado SET slug = ?, titulo = ?, contenido = ?, dirigido_a = ? WHERE id = ?',
    [slug(titulo), titulo, contenido, req.body.dirigido_a === undefined ? c.dirigido_a : destino(req.body.dirigido_a), c.id]);
  res.json(await buscar(c.id));
});

r.delete('/:id', admin, async (req, res) => {
  const c = await buscar(id(req));
  await q('UPDATE comunicado SET estado = 0 WHERE id = ?', [c.id]);   // baja logica
  res.json(await buscar(c.id));
});

r.patch('/:id/estado', admin, async (req, res) => {
  soloCampos(req.body, ['estado']);
  if (typeof req.body.estado !== 'boolean') throw new HttpError(422, 'estado debe ser true o false');
  const c = await buscar(id(req));
  await q('UPDATE comunicado SET estado = ? WHERE id = ?', [req.body.estado ? 1 : 0, c.id]);
  res.json(await buscar(c.id));
});

module.exports = r;
