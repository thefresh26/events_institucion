const { Router } = require('express');
const { requireAuth, requireRole } = require('../middlewares/auth');
const c = require('../controllers/valoracionController');

const r = Router();
r.use(requireAuth);

r.post('/postValoracion', requireRole('colegio'), c.postValoracion);
r.get('/getValoracionesByEvento/:id', c.getValoracionesByEvento);
r.delete('/deleteValoracion/:id', c.deleteValoracion);

module.exports = r;
