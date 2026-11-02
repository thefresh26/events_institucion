const Valoracion = require('../models/valoracionModel');
const { HttpError, texto, entero, soloCampos, id } = require('../utils/util');

// Un colegio califica un evento (1 a 5). Una sola valoracion por colegio y evento (campo unico compuesto).
exports.postValoracion = async (req, res) => {
  soloCampos(req.body, ['id_evento', 'puntuacion', 'comentario']);
  const idEvento = entero(req.body.id_evento, 'id_evento');
  const puntuacion = entero(req.body.puntuacion, 'puntuacion', { min: 1, max: 5 });
  const comentario = texto(req.body.comentario, 'comentario', { max: 500, requerido: false });
  const ins = await Valoracion.postValoracion(idEvento, req.user.id, puntuacion, comentario);
  res.status(201).json(await Valoracion.getValoracionById(ins.insertId));
};

// Valoraciones de un evento + promedio
exports.getValoracionesByEvento = async (req, res) => {
  const n = id(req);
  const lista = await Valoracion.getValoracionesByEvento(n);
  const promedio = lista.length ? Math.round((lista.reduce((s, v) => s + v.puntuacion, 0) / lista.length) * 10) / 10 : null;
  res.json({ id_evento: n, total: lista.length, promedio, valoraciones: lista });
};

// El dueño o el administrador la eliminan (baja logica)
exports.deleteValoracion = async (req, res) => {
  const v = await Valoracion.getValoracionActiva(id(req));
  if (!v || (req.user.rol !== 'administrador' && v.id_usuario !== req.user.id)) throw new HttpError(404, 'No encontrado');
  await Valoracion.deleteValoracion(v.id);
  res.status(204).end();
};
