import { peticion } from './api_base.js';

// GET -> numeros del panel (eventos por estado, colegios, organizadores, inscripciones)
export const obtenerResumen = () => peticion('/admin/resumen');

// GET -> organizadores registrados
export const listarOrganizadores = () => peticion('/admin/organizadores');

// PATCH -> aprueba (activo = true) o desactiva un organizador
export const activarOrganizador = (id, activo) => peticion(`/admin/organizadores/${id}/activo`, { method: 'PATCH', body: { activo } });

// GET -> todos los colegios
export const listarColegios = () => peticion('/admin/colegios');
