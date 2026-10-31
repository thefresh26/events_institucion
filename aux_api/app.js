require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const pool = require('./config/dbConfig');
const { spec } = require('./openapi');

const app = express();
const cdn = 'https://cdn.jsdelivr.net';
app.use(helmet({ contentSecurityPolicy: { directives: {   // permite cargar Swagger UI (solo en /docs) desde jsDelivr
  defaultSrc: ["'self'"], scriptSrc: ["'self'", "'unsafe-inline'", cdn], styleSrc: ["'self'", "'unsafe-inline'", cdn],
  imgSrc: ["'self'", 'data:'], connectSrc: ["'self'"] } } }));
app.use(cors({ origin: (process.env.CORS_ORIGINS || '*').split(',').map((s) => s.trim()), allowedHeaders: ['Content-Type', 'Authorization'] }));
app.use(express.json({ limit: '50kb' }));

app.get('/', (_req, res) => res.json({
  servicio: 'Conexión Escolar - API auxiliar', stack: 'Express + MySQL', documentacion: '/docs', openapi: '/openapi.json', salud: '/health',
}));
app.get('/health', async (_req, res) => {
  try { await pool.query('SELECT 1'); res.json({ status: 'ok', mysql: 'conectado' }); }
  catch { res.status(503).json({ status: 'error', mysql: 'sin conexión' }); }
});
app.get('/openapi.json', (_req, res) => res.json(spec()));
app.get('/docs', (_req, res) => res.type('html').send(`<!doctype html><html><head><meta charset="utf-8"><title>API auxiliar - Conexión Escolar</title>
<link rel="stylesheet" href="${cdn}/npm/swagger-ui-dist@5/swagger-ui.css"></head><body><div id="ui"></div>
<script src="${cdn}/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>SwaggerUIBundle({ url: '/openapi.json', dom_id: '#ui' });</script></body></html>`));

app.use('/api/aux/tipos-pqrs', require('./routes/tipoPqrsRoutes'));
app.use('/api/aux/pqrs', require('./routes/pqrsRoutes'));
app.use('/api/aux/comunicados', require('./routes/comunicadoRoutes'));
app.use('/api/aux/valoraciones', require('./routes/valoracionRoutes'));

app.use((_req, res) => res.status(404).json({ detail: 'No encontrado' }));
app.use((err, _req, res, _next) => {   // manejador unico: nunca se filtran detalles internos
  if (err.status) return res.status(err.status).json({ detail: err.message });
  if (err.type === 'entity.parse.failed') return res.status(400).json({ detail: 'JSON inválido' });
  console.error(err);
  res.status(500).json({ detail: 'Error interno del servidor' });
});

module.exports = app;
