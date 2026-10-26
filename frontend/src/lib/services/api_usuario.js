import { peticion } from './api_base.js';

// Gestion de usuarios y roles (solo administrador)

// GET -> filtros opcionales, ej. { rol: 'organizador', q: 'ana' }
export function listarUsuarios(filtros = {}) {
	const p = new URLSearchParams(Object.entries(filtros).filter(([, v]) => v)); // los filtros vacios no se envian
	return peticion('/admin/usuarios' + (p.size ? `?${p}` : ''));
}

// POST -> crea la cuenta y devuelve una contraseña temporal (se muestra una sola vez)
export const crearUsuario = (usuario) => peticion('/admin/usuarios', { method: 'POST', body: usuario });

// PATCH -> cambia nombre, apellido, rol o activo (solo lo que se envie)
export const actualizarUsuario = (id, datos) => peticion(`/admin/usuarios/${id}`, { method: 'PATCH', body: datos });

// DELETE -> borrado logico
export const eliminarUsuario = (id) => peticion(`/admin/usuarios/${id}`, { method: 'DELETE' });

// POST -> genera una nueva contraseña temporal
export const restablecerContrasena = (id) => peticion(`/admin/usuarios/${id}/restablecer`, { method: 'POST' });

// GET -> roles con sus modulos
export const listarRoles = () => peticion('/admin/roles');

// PUT -> reemplaza los modulos (nombres) de un rol
export const asignarModulos = (idRol, modulos) => peticion(`/admin/roles/${idRol}/modulos`, { method: 'PUT', body: { modulos } });
