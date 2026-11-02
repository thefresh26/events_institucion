const Comunicado = require('../models/comunicadoModel');
const { HttpError, texto, soloCampos, id, slug } = require('../utils/util');

const DEST = ['todos', 'organizador', 'colegio'];
const buscar = async (n) => { const c = await Comunicado.getComunicadoById(n); if (!c) throw new HttpError(404, 'No encontrado'); return c; };
const destino = (v) => { if (v !== undefined && !DEST.includes(v)) throw new HttpError(422, `dirigido_a debe ser: ${DEST.join(', ')}`); return v || 'todos'; };

// Cada usuario ve los comunicados para "todos" y los de su rol; el administrador ve todos los activos.
exports.getComunicados = async (req, res) =>
  res.json(req.user.rol === 'administrador' ? await Comunicado.getComunicados() : await Comunicado.getComunicadosByRol(req.user.rol));

exports.postComunicado = async (req, res) => {
  soloCampos(req.body, ['titulo', 'contenido', 'dirigido_a']);
  const titulo = texto(req.body.titulo, 'titulo', { min: 3, max: 150 });
  const contenido = texto(req.body.contenido, 'contenido', { min: 5, max: 2000 });
  const ins = await Comunicado.postComunicado(slug(titulo), titulo, contenido, destino(req.body.dirigido_a), req.user.id);   // slug unico: mismo titulo = 409
  res.status(201).json(await buscar(ins.insertId));
};

exports.putComunicado = async (req, res) => {
  soloCampos(req.body, ['titulo', 'contenido', 'dirigido_a']);
  const c = await buscar(id(req));
  const titulo = req.body.titulo === undefined ? c.titulo : texto(req.body.titulo, 'titulo', { min: 3, max: 150 });
  const contenido = req.body.contenido === undefined ? c.contenido : texto(req.body.contenido, 'contenido', { min: 5, max: 2000 });
  await Comunicado.putComunicado(c.id, slug(titulo), titulo, contenido, req.body.dirigido_a === undefined ? c.dirigido_a : destino(req.body.dirigido_a));
  res.json(await buscar(c.id));
};

exports.deleteComunicado = async (req, res) => {
  const c = await buscar(id(req));
  await Comunicado.setEstadoComunicado(c.id, 0);   // baja logica
  res.json(await buscar(c.id));
};

exports.patchEstadoComunicado = async (req, res) => {
  soloCampos(req.body, ['estado']);
  if (typeof req.body.estado !== 'boolean') throw new HttpError(422, 'estado debe ser true o false');
  const c = await buscar(id(req));
  await Comunicado.setEstadoComunicado(c.id, req.body.estado ? 1 : 0);
  res.json(await buscar(c.id));
};
