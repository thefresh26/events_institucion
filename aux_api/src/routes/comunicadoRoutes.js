const { Router } = require('express');
const { requireAuth, requireRole } = require('../middlewares/auth');
const c = require('../controllers/comunicadoController');

const r = Router();
r.use(requireAuth);
const admin = requireRole('administrador');

r.get('/getComunicados', c.getComunicados);
r.post('/postComunicado', admin, c.postComunicado);
r.put('/putComunicado/:id', admin, c.putComunicado);
r.delete('/deleteComunicado/:id', admin, c.deleteComunicado);
r.patch('/patchEstadoComunicado/:id', admin, c.patchEstadoComunicado);

module.exports = r;
