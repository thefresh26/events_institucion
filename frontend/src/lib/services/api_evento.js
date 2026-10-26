import { peticion } from './api_base.js';

// ---------------- Organizador ----------------
// GET -> eventos del organizador que inicio sesion
export const listarMisEventos = () => peticion('/organizador/eventos');

// POST -> crea un evento (nace en borrador)
export const crearEvento = (evento) => peticion('/organizador/eventos', { method: 'POST', body: evento });

// PUT -> edita un evento en borrador o rechazado (vuelve a borrador)
export const actualizarEvento = (id, evento) => peticion(`/organizador/eventos/${id}`, { method: 'PUT', body: evento });

// DELETE -> borrado logico (solo borrador o rechazado)
export const eliminarEvento = (id) => peticion(`/organizador/eventos/${id}`, { method: 'DELETE' });

// POST -> envia el evento al administrador para que lo apruebe
export const enviarEvento = (id) => peticion(`/organizador/eventos/${id}/enviar`, { method: 'POST' });

// ---------------- Colegio ----------------
// GET -> eventos publicados de su organizador, con "mi_inscripcion"
export const listarEventosDisponibles = () => peticion('/colegio/eventos');

// ---------------- Administrador ----------------
// GET -> todos los eventos; estado opcional: 'pendiente', 'publicado', ...
export const listarEventos = (estado = '') => peticion('/admin/eventos' + (estado ? `?estado=${estado}` : ''));

// PATCH -> decision: 'publicado' o 'rechazado'
export const decidirEvento = (id, decision) => peticion(`/admin/eventos/${id}/decision`, { method: 'PATCH', body: { decision } });

// POST -> cierra un evento publicado
export const cerrarEvento = (id) => peticion(`/admin/eventos/${id}/cerrar`, { method: 'POST' });
