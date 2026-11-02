const Tipo = require('../models/tipoPqrsModel');
const Pqrs = require('../models/pqrsModel');
const { HttpError, texto, entero, soloCampos, id } = require('../utils/util');

const esAdmin = (u) => u.rol === 'administrador';

// Un usuario solo ve sus PQRS; el administrador ve todas. 404 (no 403) si no es suya: no revela que existe.
async function visible(req) {
  const p = await Pqrs.getPqrsById(id(req));
  if (!p || (!esAdmin(req.user) && p.id_usuario !== req.user.id)) throw new HttpError(404, 'No encontrado');
  return p;
}

exports.postPqrs = async (req, res) => {
  soloCampos(req.body, ['id_tipo', 'asunto', 'mensaje']);
  const idTipo = entero(req.body.id_tipo, 'id_tipo');
  const asunto = texto(req.body.asunto, 'asunto', { min: 3, max: 150 });
  const mensaje = texto(req.body.mensaje, 'mensaje', { min: 5, max: 1000 });
  if (!(await Tipo.getTipoActivo(idTipo))) throw new HttpError(422, 'Tipo de PQRS inválido');
  const radicado = `PQRS-${new Date().getFullYear()}-${Date.now().toString(36).toUpperCase()}`;  // unico
  const ins = await Pqrs.postPqrs(radicado, idTipo, req.user.id, asunto, mensaje);
  res.status(201).json(await visible({ params: { id: ins.insertId }, user: req.user }));
};

exports.getPqrs = async (req, res) =>
  res.json(esAdmin(req.user) ? await Pqrs.getPqrs() : await Pqrs.getPqrsByUsuario(req.user.id));

exports.getPqrsById = async (req, res) => res.json(await visible(req));

exports.responderPqrs = async (req, res) => {
  soloCampos(req.body, ['respuesta']);
  const respuesta = texto(req.body.respuesta, 'respuesta', { min: 3, max: 1000 });
  const p = await visible(req);
  await Pqrs.responderPqrs(p.id, respuesta, req.user.id);
  res.json(await visible(req));
};

exports.deletePqrs = async (req, res) => {
  const p = await visible(req);
  await Pqrs.deletePqrs(p.id);   // baja logica
  res.status(204).end();
};
