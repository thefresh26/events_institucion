const { q, uno } = require('../utils/util');

exports.getTipos = () => q('SELECT * FROM tipo_pqrs WHERE estado = 1 ORDER BY id');
exports.getTipoById = (id) => uno('SELECT * FROM tipo_pqrs WHERE id = ?', [id]);
exports.getTipoActivo = (id) => uno('SELECT id FROM tipo_pqrs WHERE id = ? AND estado = 1', [id]);
exports.postTipo = (nombre, descripcion) => q('INSERT INTO tipo_pqrs (nombre, descripcion) VALUES (?, ?)', [nombre, descripcion]);
exports.putTipo = (id, nombre, descripcion) => q('UPDATE tipo_pqrs SET nombre = ?, descripcion = ? WHERE id = ?', [nombre, descripcion, id]);
exports.setEstadoTipo = (id, estado) => q('UPDATE tipo_pqrs SET estado = ? WHERE id = ?', [estado, id]);   // baja logica: estado = 0
