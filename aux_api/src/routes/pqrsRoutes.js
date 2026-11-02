const { Router } = require('express');
const { requireAuth, requireRole } = require('../middlewares/auth');
const c = require('../controllers/pqrsController');

const r = Router();
r.use(requireAuth);

r.post('/postPqrs', c.postPqrs);
r.get('/getPqrs', c.getPqrs);
r.get('/getPqrsById/:id', c.getPqrsById);
r.patch('/responderPqrs/:id', requireRole('administrador'), c.responderPqrs);
r.delete('/deletePqrs/:id', requireRole('administrador'), c.deletePqrs);

module.exports = r;
