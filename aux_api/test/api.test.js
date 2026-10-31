// Pruebas de la API auxiliar. Necesitan un MySQL con la base creada (npm run init-db) y las variables del .env.
process.env.SECRET_KEY = process.env.SECRET_KEY || 'test-secret';
const test = require('node:test');
const assert = require('node:assert/strict');
const jwt = require('jsonwebtoken');
const app = require('../app');
const pool = require('../config/dbConfig');

let server, base;
const token = (sub, rol, extra = {}) => jwt.sign({ sub: String(sub), rol }, process.env.SECRET_KEY, { algorithm: 'HS256', expiresIn: '1h', ...extra });
const ADMIN = token(1, 'administrador'), COLEGIO = token(7, 'colegio'), COLEGIO2 = token(8, 'colegio'), ORG = token(3, 'organizador');
const api = async (method, path, tk, body) => {
  const r = await fetch(base + path, { method, headers: { 'Content-Type': 'application/json', ...(tk ? { Authorization: `Bearer ${tk}` } : {}) }, body: body ? JSON.stringify(body) : undefined });
  const t = await r.text();
  return { status: r.status, body: t ? JSON.parse(t) : null };
};
const sufijo = Date.now().toString(36);

test.before(async () => { server = app.listen(0); base = `http://127.0.0.1:${server.address().port}`; });
test.after(async () => { server.close(); await pool.end(); });

test('todas las tablas tienen estado, creado y actualizado, PK y campos unicos', async () => {
  const [cols] = await pool.query("SELECT table_name t, column_name c FROM information_schema.columns WHERE table_schema = DATABASE() AND column_name IN ('estado','creado','actualizado')");
  const [tablas] = await pool.query("SELECT table_name t FROM information_schema.tables WHERE table_schema = DATABASE()");
  assert.ok(tablas.length >= 3);
  for (const { t } of tablas) for (const c of ['estado', 'creado', 'actualizado']) assert.ok(cols.some((x) => x.t === t && x.c === c), `${t} sin ${c}`);
  const [pk] = await pool.query("SELECT COUNT(DISTINCT table_name) n FROM information_schema.table_constraints WHERE table_schema = DATABASE() AND constraint_type = 'PRIMARY KEY'");
  const [uq] = await pool.query("SELECT COUNT(DISTINCT table_name) n FROM information_schema.table_constraints WHERE table_schema = DATABASE() AND constraint_type = 'UNIQUE'");
  assert.equal(pk[0].n, tablas.length); assert.equal(uq[0].n, tablas.length);
});

test('salud, documentacion y JWT', async () => {
  assert.equal((await api('GET', '/health')).body.mysql, 'conectado');
  assert.ok((await api('GET', '/openapi.json')).body.paths['/api/aux/pqrs']);
  assert.equal((await fetch(base + '/docs')).status, 200);
  assert.equal((await api('GET', '/api/aux/pqrs')).status, 401);                                          // sin token
  assert.equal((await api('GET', '/api/aux/pqrs', ADMIN.slice(0, -3) + 'abc')).status, 401);              // firma alterada
  assert.equal((await api('GET', '/api/aux/pqrs', token(1, 'administrador', { expiresIn: -10 }))).status, 401);   // vencido
  assert.equal((await api('GET', '/api/aux/pqrs', jwt.sign({ sub: '1', rol: 'administrador' }, 'otra-clave'))).status, 401);
  const [cab, , firma] = COLEGIO.split('.');                                                               // contenido cambiado sin volver a firmar:
  const subido = Buffer.from(JSON.stringify({ sub: '7', rol: 'administrador', exp: Math.floor(Date.now() / 1000) + 3600 })).toString('base64url');
  assert.equal((await api('GET', '/api/aux/pqrs', `${cab}.${subido}.${firma}`)).status, 401);              // colegio que se "sube" a administrador
  assert.equal((await api('GET', '/api/aux/pqrs', ADMIN)).status, 200);
});

test('sin SECRET_KEY (o con la de ejemplo) el servidor no arranca y lo explica', () => {
  const { spawnSync } = require('node:child_process');
  for (const valor of ['', 'cambia-esto']) {
    const r = spawnSync(process.execPath, ['index.js'], { cwd: require('node:path').join(__dirname, '..'), timeout: 10000,
      env: { ...process.env, SECRET_KEY: valor, PORT: '0' }, encoding: 'utf8' });
    assert.equal(r.status, 1, `con SECRET_KEY="${valor}" debio salir con codigo 1`);
    assert.match(r.stderr, /falta SECRET_KEY/);
  }
});

test('tipos de PQRS: CRUD, unico, baja logica y restaurar', async () => {
  assert.equal((await api('POST', '/api/aux/tipos-pqrs', COLEGIO, { nombre: 'X' })).status, 403);
  const c = await api('POST', '/api/aux/tipos-pqrs', ADMIN, { nombre: 'Tipo ' + sufijo });
  assert.equal(c.status, 201); assert.equal(c.body.estado, 1); assert.ok(c.body.creado && c.body.actualizado);
  assert.equal((await api('POST', '/api/aux/tipos-pqrs', ADMIN, { nombre: 'Tipo ' + sufijo })).status, 409);        // unico
  assert.equal((await api('POST', '/api/aux/tipos-pqrs', ADMIN, { nombre: 'Otro', estado: 0 })).status, 422);       // estado no se envia al crear
  assert.equal((await api('PUT', `/api/aux/tipos-pqrs/${c.body.id}`, ADMIN, { descripcion: 'nueva' })).body.descripcion, 'nueva');
  assert.equal((await api('DELETE', `/api/aux/tipos-pqrs/${c.body.id}`, ADMIN)).body.estado, 0);                    // baja logica
  assert.ok(!(await api('GET', '/api/aux/tipos-pqrs', ADMIN)).body.some((t) => t.id === c.body.id));               // ya no se lista
  const [f] = (await pool.query('SELECT estado FROM tipo_pqrs WHERE id = ?', [c.body.id]))[0];
  assert.equal(f.estado, 0);                                                                                         // pero la fila existe
  assert.equal((await api('PATCH', `/api/aux/tipos-pqrs/${c.body.id}/estado`, ADMIN, { estado: true })).body.estado, 1);
});

test('PQRS: el usuario solo ve las suyas, el admin responde y elimina', async () => {
  const tipo = (await api('GET', '/api/aux/tipos-pqrs', COLEGIO)).body[0].id;
  assert.equal((await api('POST', '/api/aux/pqrs', COLEGIO, { id_tipo: 9999, asunto: 'Hola', mensaje: 'Mensaje largo' })).status, 422);
  const p = await api('POST', '/api/aux/pqrs', COLEGIO, { id_tipo: tipo, asunto: 'No llega el correo', mensaje: 'No recibí la confirmación' });
  assert.equal(p.status, 201); assert.match(p.body.radicado, /^PQRS-\d{4}-/); assert.equal(p.body.id_usuario, 7);
  assert.equal((await api('GET', `/api/aux/pqrs/${p.body.id}`, COLEGIO2)).status, 404);                              // IDOR bloqueado
  assert.ok((await api('GET', '/api/aux/pqrs', COLEGIO)).body.some((x) => x.id === p.body.id));
  assert.ok(!(await api('GET', '/api/aux/pqrs', COLEGIO2)).body.some((x) => x.id === p.body.id));
  assert.equal((await api('PATCH', `/api/aux/pqrs/${p.body.id}/responder`, COLEGIO, { respuesta: 'yo mismo' })).status, 403);
  const r = await api('PATCH', `/api/aux/pqrs/${p.body.id}/responder`, ADMIN, { respuesta: 'Ya lo revisamos' });
  assert.equal(r.body.respuesta, 'Ya lo revisamos'); assert.equal(r.body.id_respondio, 1); assert.ok(r.body.respondida_en);
  assert.equal((await api('DELETE', `/api/aux/pqrs/${p.body.id}`, ADMIN)).status, 204);
  assert.equal((await api('GET', `/api/aux/pqrs/${p.body.id}`, ADMIN)).status, 404);
});

test('comunicados: filtrados por rol y baja logica', async () => {
  const t = 'Aviso ' + sufijo;
  const c = await api('POST', '/api/aux/comunicados', ADMIN, { titulo: t, contenido: 'Solo para colegios', dirigido_a: 'colegio' });
  assert.equal(c.status, 201); assert.equal(c.body.slug, ('aviso-' + sufijo));
  assert.equal((await api('POST', '/api/aux/comunicados', ADMIN, { titulo: t, contenido: 'Repetido' })).status, 409);   // slug unico
  assert.equal((await api('POST', '/api/aux/comunicados', ORG, { titulo: 'x y z', contenido: 'abcdef' })).status, 403);
  assert.equal((await api('POST', '/api/aux/comunicados', ADMIN, { titulo: 'Malo', contenido: 'abcdef', dirigido_a: 'nadie' })).status, 422);
  assert.ok((await api('GET', '/api/aux/comunicados', COLEGIO)).body.some((x) => x.id === c.body.id));
  assert.ok(!(await api('GET', '/api/aux/comunicados', ORG)).body.some((x) => x.id === c.body.id));                    // no es para organizador
  await api('DELETE', `/api/aux/comunicados/${c.body.id}`, ADMIN);
  assert.ok(!(await api('GET', '/api/aux/comunicados', COLEGIO)).body.some((x) => x.id === c.body.id));
});

test('valoraciones: 1 a 5, una por colegio y evento, promedio', async () => {
  const ev = 900000 + Math.floor(Math.random() * 90000);
  assert.equal((await api('POST', '/api/aux/valoraciones', ORG, { id_evento: ev, puntuacion: 5 })).status, 403);     // solo colegios
  assert.equal((await api('POST', '/api/aux/valoraciones', COLEGIO, { id_evento: ev, puntuacion: 6 })).status, 422);
  const a = await api('POST', '/api/aux/valoraciones', COLEGIO, { id_evento: ev, puntuacion: 5, comentario: 'Excelente' });
  assert.equal(a.status, 201);
  assert.equal((await api('POST', '/api/aux/valoraciones', COLEGIO, { id_evento: ev, puntuacion: 4 })).status, 409);  // unico (evento, usuario)
  await api('POST', '/api/aux/valoraciones', COLEGIO2, { id_evento: ev, puntuacion: 3 });
  const lista = await api('GET', `/api/aux/valoraciones/evento/${ev}`, ORG);
  assert.equal(lista.body.total, 2); assert.equal(lista.body.promedio, 4);
  assert.equal((await api('DELETE', `/api/aux/valoraciones/${a.body.id}`, COLEGIO2)).status, 404);                   // no es suya
  assert.equal((await api('DELETE', `/api/aux/valoraciones/${a.body.id}`, COLEGIO)).status, 204);
  assert.equal((await api('GET', `/api/aux/valoraciones/evento/${ev}`, ORG)).body.total, 1);
});
