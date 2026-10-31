const { Router } = require('express');
const { requireAuth, requireRole } = require('../middlewares/auth');
const c = require('../controllers/pqrsController');

const r = Router();
r.use(requireAuth);

r.post('/', c.postPqrs);
r.get('/', c.getPqrs);
r.get('/:id', c.getPqrsById);
r.patch('/:id/responder', requireRole('administrador'), c.responderPqrs);
r.delete('/:id', requireRole('administrador'), c.deletePqrs);

module.exports = r;
