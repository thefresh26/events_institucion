import { peticion } from './api_base.js';

// POST -> inicia sesion; el servidor deja el token en una cookie HttpOnly y devuelve el usuario
export const iniciarSesion = (correo, contrasena) => peticion('/auth/login', { method: 'POST', body: { correo, contrasena } });

// POST -> borra la cookie de sesion
export const cerrarSesion = () => peticion('/auth/logout', { method: 'POST' });

// GET -> usuario de la sesion actual con su rol y modulos (401 si no hay sesion)
export const obtenerSesion = () => peticion('/auth/me');

// POST -> registro publico de organizadores (queda pendiente de aprobacion)
export const registrarOrganizador = (datos) => peticion('/auth/registro/organizador', { method: 'POST', body: datos });

// POST -> cambia la contraseña del usuario que inicio sesion
export const cambiarContrasena = (actual, nueva) => peticion('/auth/cambiar-contrasena', { method: 'POST', body: { actual, nueva } });
