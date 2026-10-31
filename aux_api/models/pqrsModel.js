const { q, uno } = require('../utils/util');

const BASE = 'SELECT p.*, t.nombre AS tipo FROM pqrs p JOIN tipo_pqrs t ON t.id = p.id_tipo WHERE p.estado = 1';

exports.getPqrs = () => q(`${BASE} ORDER BY p.id DESC LIMIT 500`);
exports.getPqrsByUsuario = (idUsuario) => q(`${BASE} AND p.id_usuario = ? ORDER BY p.id DESC LIMIT 500`, [idUsuario]);
exports.getPqrsById = (id) => uno(`${BASE} AND p.id = ?`, [id]);
exports.postPqrs = (radicado, idTipo, idUsuario, asunto, mensaje) =>
  q('INSERT INTO pqrs (radicado, id_tipo, id_usuario, asunto, mensaje) VALUES (?, ?, ?, ?, ?)', [radicado, idTipo, idUsuario, asunto, mensaje]);
exports.responderPqrs = (id, respuesta, idRespondio) =>
  q('UPDATE pqrs SET respuesta = ?, id_respondio = ?, respondida_en = NOW() WHERE id = ?', [respuesta, idRespondio, id]);
exports.deletePqrs = (id) => q('UPDATE pqrs SET estado = 0 WHERE id = ?', [id]);   // baja logica
