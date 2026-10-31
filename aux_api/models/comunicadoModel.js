const { q, uno } = require('../utils/util');

const BASE = 'SELECT * FROM comunicado WHERE estado = 1';

exports.getComunicados = () => q(`${BASE} ORDER BY id DESC LIMIT 200`);
exports.getComunicadosByRol = (rol) => q(`${BASE} AND dirigido_a IN ('todos', ?) ORDER BY id DESC LIMIT 200`, [rol]);
exports.getComunicadoById = (id) => uno('SELECT * FROM comunicado WHERE id = ?', [id]);
exports.postComunicado = (slug, titulo, contenido, dirigidoA, idAutor) =>
  q('INSERT INTO comunicado (slug, titulo, contenido, dirigido_a, id_autor) VALUES (?, ?, ?, ?, ?)', [slug, titulo, contenido, dirigidoA, idAutor]);
exports.putComunicado = (id, slug, titulo, contenido, dirigidoA) =>
  q('UPDATE comunicado SET slug = ?, titulo = ?, contenido = ?, dirigido_a = ? WHERE id = ?', [slug, titulo, contenido, dirigidoA, id]);
exports.setEstadoComunicado = (id, estado) => q('UPDATE comunicado SET estado = ? WHERE id = ?', [estado, id]);   // baja logica: estado = 0
