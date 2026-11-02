const { Router } = require('express');
const { requireAuth, requireRole } = require('../middlewares/auth');
const c = require('../controllers/tipoPqrsController');

const r = Router();
const admin = requireRole('administrador');

r.get('/getTipos', requireAuth, c.getTipos);
r.post('/postTipo', requireAuth, admin, c.postTipo);
r.put('/putTipo/:id', requireAuth, admin, c.putTipo);
r.delete('/deleteTipo/:id', requireAuth, admin, c.deleteTipo);
r.patch('/patchEstadoTipo/:id', requireAuth, admin, c.patchEstadoTipo);

module.exports = r;
