const jwt = require('jsonwebtoken');

// Valida el JWT que emite la API principal (FastAPI) en POST /api/v1/auth/login.
// Misma clave (SECRET_KEY) y algoritmo HS256. Carga del token: { sub: id_usuario, rol, exp }.
function requireAuth(req, res, next) {
  const h = req.headers.authorization || '';
  const token = h.startsWith('Bearer ') ? h.slice(7) : null;
  if (!token) return res.status(401).json({ detail: 'Falta el token (Authorization: Bearer <jwt>)' });
  try {
    const p = jwt.verify(token, process.env.SECRET_KEY, { algorithms: ['HS256'] }); // verifica firma y expiracion
    if (!p.sub || !p.rol) return res.status(401).json({ detail: 'Token sin usuario o rol' });
    req.user = { id: Number(p.sub), rol: p.rol };
    next();
  } catch {
    res.status(401).json({ detail: 'Token inválido o vencido' });
  }
}

// Autorizacion por rol: requireRole('administrador'), requireRole('colegio', 'organizador')...
const requireRole = (...roles) => (req, res, next) =>
  roles.includes(req.user.rol) ? next() : res.status(403).json({ detail: 'No tienes permisos para esta acción' });

module.exports = { requireAuth, requireRole };
