import { peticion } from './api_base.js';

// ---------------- Administrador ----------------
// GET -> numeros del panel (eventos por estado, colegios, organizadores, inscripciones)
export const obtenerResumen = () => peticion('/admin/resumen');

// GET -> organizadores registrados
export const listarOrganizadores = () => peticion('/admin/organizadores');

// PATCH -> aprueba (activo = true) o desactiva un organizador
export const activarOrganizador = (id, activo) => peticion(`/admin/organizadores/${id}/activo`, { method: 'PATCH', body: { activo } });

// GET -> todos los colegios
export const listarColegios = () => peticion('/admin/colegios');

// ---------------- Organizador: sus colegios ----------------
// GET -> colegios que registro el organizador que inicio sesion
export const listarMisColegios = () => peticion('/organizador/colegios');

// POST -> registra un colegio y devuelve su contraseña temporal (se muestra una sola vez)
export const crearColegio = (colegio) => peticion('/organizador/colegios', { method: 'POST', body: colegio });

// PATCH -> activa o desactiva el acceso del colegio
export const activarColegio = (id, activo) => peticion(`/organizador/colegios/${id}/activo`, { method: 'PATCH', body: { activo } });

// DELETE -> borrado logico del colegio
export const eliminarColegio = (id) => peticion(`/organizador/colegios/${id}`, { method: 'DELETE' });
