const Tipo = require('../models/tipoPqrsModel');
const { HttpError, texto, soloCampos, id } = require('../utils/util');

const buscar = async (n) => { const t = await Tipo.getTipoById(n); if (!t) throw new HttpError(404, 'No encontrado'); return t; };

// Cualquier usuario autenticado ve los tipos activos (estado = 1)
exports.getTipos = async (_req, res) => res.json(await Tipo.getTipos());

exports.postTipo = async (req, res) => {
  soloCampos(req.body, ['nombre', 'descripcion']);
  const nombre = texto(req.body.nombre, 'nombre', { max: 50 });
  const descripcion = texto(req.body.descripcion, 'descripcion', { requerido: false });
  const ins = await Tipo.postTipo(nombre, descripcion);
  res.status(201).json(await buscar(ins.insertId));
};

exports.putTipo = async (req, res) => {
  soloCampos(req.body, ['nombre', 'descripcion']);
  const n = id(req); const t = await buscar(n);
  const nombre = req.body.nombre === undefined ? t.nombre : texto(req.body.nombre, 'nombre', { max: 50 });
  const descripcion = req.body.descripcion === undefined ? t.descripcion : texto(req.body.descripcion, 'descripcion', { requerido: false });
  await Tipo.putTipo(n, nombre, descripcion);
  res.json(await buscar(n));
};

// Baja logica: estado = 0. La fila NO se borra.
exports.deleteTipo = async (req, res) => {
  const n = id(req); await buscar(n);
  await Tipo.setEstadoTipo(n, 0);
  res.json(await buscar(n));
};

// Manipular el campo estado a mano (0 = eliminado, 1 = restaurar)
exports.patchEstadoTipo = async (req, res) => {
  soloCampos(req.body, ['estado']);
  if (typeof req.body.estado !== 'boolean') throw new HttpError(422, 'estado debe ser true o false');
  const n = id(req); await buscar(n);
  await Tipo.setEstadoTipo(n, req.body.estado ? 1 : 0);
  res.json(await buscar(n));
};
