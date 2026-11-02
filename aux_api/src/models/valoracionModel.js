const { q, uno } = require('../utils/util');

exports.postValoracion = (idEvento, idUsuario, puntuacion, comentario) =>
  q('INSERT INTO valoracion_evento (id_evento, id_usuario, puntuacion, comentario) VALUES (?, ?, ?, ?)', [idEvento, idUsuario, puntuacion, comentario]);
exports.getValoracionById = (id) => uno('SELECT * FROM valoracion_evento WHERE id = ?', [id]);
exports.getValoracionActiva = (id) => uno('SELECT * FROM valoracion_evento WHERE id = ? AND estado = 1', [id]);
exports.getValoracionesByEvento = (idEvento) =>
  q('SELECT id, id_evento, puntuacion, comentario, creado FROM valoracion_evento WHERE id_evento = ? AND estado = 1 ORDER BY id DESC LIMIT 500', [idEvento]);
exports.deleteValoracion = (id) => q('UPDATE valoracion_evento SET estado = 0 WHERE id = ?', [id]);   // baja logica
