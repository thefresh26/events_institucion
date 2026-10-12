// Especificacion OpenAPI generada desde una tabla compacta (para la documentacion interactiva en /docs).
const R = (rol) => ({ A: 'administrador', U: 'cualquier usuario autenticado', C: 'colegio', D: 'dueño o administrador', '-': 'público' }[rol]);

// [metodo, ruta, resumen, quien, ejemplo de cuerpo]
const RUTAS = [
  ['get', '/health', 'Estado del servicio y de la conexión a MySQL', '-'],
  ['get', '/api/aux/tipos-pqrs', 'Listar tipos de PQRS activos (estado=1)', 'U'],
  ['post', '/api/aux/tipos-pqrs', 'Crear tipo de PQRS', 'A', { nombre: 'Felicitación', descripcion: 'Reconocimiento al servicio' }],
  ['put', '/api/aux/tipos-pqrs/{id}', 'Editar tipo de PQRS', 'A', { nombre: 'Felicitación', descripcion: 'Texto nuevo' }],
  ['delete', '/api/aux/tipos-pqrs/{id}', 'Eliminar tipo de PQRS (baja lógica: estado=0)', 'A'],
  ['patch', '/api/aux/tipos-pqrs/{id}/estado', 'Cambiar el campo estado (true restaura)', 'A', { estado: true }],
  ['post', '/api/aux/pqrs', 'Radicar una PQRS', 'U', { id_tipo: 1, asunto: 'No me llega el correo', mensaje: 'Inscribí a mi colegio y no recibí confirmación.' }],
  ['get', '/api/aux/pqrs', 'Listar mis PQRS (el administrador ve todas)', 'U'],
  ['get', '/api/aux/pqrs/{id}', 'Ver una PQRS', 'D'],
  ['patch', '/api/aux/pqrs/{id}/responder', 'Responder una PQRS', 'A', { respuesta: 'Ya revisamos tu caso, gracias.' }],
  ['delete', '/api/aux/pqrs/{id}', 'Eliminar una PQRS (baja lógica)', 'A'],
  ['get', '/api/aux/comunicados', 'Listar comunicados de mi rol', 'U'],
  ['post', '/api/aux/comunicados', 'Publicar comunicado', 'A', { titulo: 'Mantenimiento programado', contenido: 'El sábado la plataforma no estará disponible de 2 a 4 am.', dirigido_a: 'todos' }],
  ['put', '/api/aux/comunicados/{id}', 'Editar comunicado', 'A', { titulo: 'Mantenimiento programado', contenido: 'Texto actualizado', dirigido_a: 'colegio' }],
  ['delete', '/api/aux/comunicados/{id}', 'Eliminar comunicado (baja lógica)', 'A'],
  ['patch', '/api/aux/comunicados/{id}/estado', 'Cambiar el campo estado', 'A', { estado: true }],
  ['post', '/api/aux/valoraciones', 'Valorar un evento (1 a 5)', 'C', { id_evento: 1, puntuacion: 5, comentario: 'Muy bien organizado' }],
  ['get', '/api/aux/valoraciones/evento/{id}', 'Valoraciones y promedio de un evento', 'U'],
  ['delete', '/api/aux/valoraciones/{id}', 'Eliminar una valoración (baja lógica)', 'D'],
];

function spec() {
  const paths = {};
  for (const [m, p, resumen, quien, ej] of RUTAS) {
    const op = {
      summary: resumen, description: `Quién puede: ${R(quien)}`,
      tags: [p.split('/')[3] || 'sistema'],
      parameters: [...p.matchAll(/{(\w+)}/g)].map((x) => ({ name: x[1], in: 'path', required: true, schema: { type: 'integer' } })),
      responses: { 200: { description: 'OK' }, 401: { description: 'Sin token o token inválido' }, 403: { description: 'Sin permisos' }, 404: { description: 'No encontrado' }, 422: { description: 'Datos inválidos' } },
    };
    if (quien !== '-') op.security = [{ bearer: [] }];
    if (ej) op.requestBody = { required: true, content: { 'application/json': { example: ej } } };
    (paths[p] ||= {})[m] = op;
  }
  return {
    openapi: '3.0.3',
    info: { title: 'Conexión Escolar - API auxiliar (Express + MySQL)', version: '1.0.0',
      description: 'Valida los mismos JWT que la API principal (FastAPI). Obtén un token con POST /api/v1/auth/login de la API principal y pégalo en Authorize.' },
    components: { securitySchemes: { bearer: { type: 'http', scheme: 'bearer', bearerFormat: 'JWT' } } },
    paths,
  };
}
module.exports = { spec };
