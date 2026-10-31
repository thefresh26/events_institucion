const { Router } = require('express');
const { requireAuth, requireRole } = require('../middlewares/auth');
const c = require('../controllers/comunicadoController');

const r = Router();
r.use(requireAuth);
const admin = requireRole('administrador');

r.get('/', c.getComunicados);
r.post('/', admin, c.postComunicado);
r.put('/:id', admin, c.putComunicado);
r.delete('/:id', admin, c.deleteComunicado);
r.patch('/:id/estado', admin, c.patchEstadoComunicado);

module.exports = r;
