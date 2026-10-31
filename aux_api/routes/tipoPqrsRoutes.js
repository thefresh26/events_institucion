const { Router } = require('express');
const { requireAuth, requireRole } = require('../middlewares/auth');
const c = require('../controllers/tipoPqrsController');

const r = Router();
const admin = requireRole('administrador');

r.get('/', requireAuth, c.getTipos);
r.post('/', requireAuth, admin, c.postTipo);
r.put('/:id', requireAuth, admin, c.putTipo);
r.delete('/:id', requireAuth, admin, c.deleteTipo);
r.patch('/:id/estado', requireAuth, admin, c.patchEstadoTipo);

module.exports = r;
