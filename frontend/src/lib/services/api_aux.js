import { peticion } from './api_base.js';

// API auxiliar (Express + MySQL). El navegador solo habla con la API principal: ella reenvia estas
// peticiones a Express con el token de la sesion (rutas_aux.py), por eso todas empiezan por /aux.
const A = '/aux';

// PQRS --------------------------------------------------------------------------------------------
export const listarTipos = () => peticion(`${A}/tipos-pqrs/getTipos`);
export const listarPqrs = () => peticion(`${A}/pqrs/getPqrs`); // cada usuario ve las suyas; el administrador, todas
export const radicarPqrs = (pqrs) => peticion(`${A}/pqrs/postPqrs`, { method: 'POST', body: pqrs });
export const responderPqrs = (id, respuesta) => peticion(`${A}/pqrs/responderPqrs/${id}`, { method: 'PATCH', body: { respuesta } });
export const eliminarPqrs = (id) => peticion(`${A}/pqrs/deletePqrs/${id}`, { method: 'DELETE' });

// Comunicados -------------------------------------------------------------------------------------
export const listarComunicados = () => peticion(`${A}/comunicados/getComunicados`); // segun el rol
export const crearComunicado = (c) => peticion(`${A}/comunicados/postComunicado`, { method: 'POST', body: c });
export const actualizarComunicado = (id, c) => peticion(`${A}/comunicados/putComunicado/${id}`, { method: 'PUT', body: c });
export const eliminarComunicado = (id) => peticion(`${A}/comunicados/deleteComunicado/${id}`, { method: 'DELETE' });

// Valoraciones ------------------------------------------------------------------------------------
export const valoracionesDeEvento = (idEvento) => peticion(`${A}/valoraciones/getValoracionesByEvento/${idEvento}`);
export const valorarEvento = (v) => peticion(`${A}/valoraciones/postValoracion`, { method: 'POST', body: v });
export const eliminarValoracion = (id) => peticion(`${A}/valoraciones/deleteValoracion/${id}`, { method: 'DELETE' });
