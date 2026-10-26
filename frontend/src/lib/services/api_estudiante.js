import { peticion } from './api_base.js';

const URL = '/colegio/estudiantes';

// GET -> estudiantes del colegio que inicio sesion (documento enmascarado)
export const listarEstudiantes = () => peticion(URL);

// POST -> registra un estudiante (con la autorizacion del acudiente)
export const crearEstudiante = (estudiante) => peticion(URL, { method: 'POST', body: estudiante });

// DELETE -> lo retira (borrado logico)
export const eliminarEstudiante = (id) => peticion(`${URL}/${id}`, { method: 'DELETE' });
