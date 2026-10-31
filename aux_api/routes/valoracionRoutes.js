const { Router } = require('express');
const { requireAuth, requireRole } = require('../middlewares/auth');
const c = require('../controllers/valoracionController');

const r = Router();
r.use(requireAuth);

r.post('/', requireRole('colegio'), c.postValoracion);
r.get('/evento/:id', c.getValoracionesByEvento);
r.delete('/:id', c.deleteValoracion);

module.exports = r;
