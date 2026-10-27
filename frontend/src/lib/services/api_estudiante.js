import { peticion } from './api_base.js';

const URL = '/colegio/estudiantes';

// GET -> estudiantes del colegio que inicio sesion (documento enmascarado)
export const listarEstudiantes = () => peticion(URL);

// POST -> registra un estudiante (con la autorizacion del acudiente)
export const crearEstudiante = (estudiante) => peticion(URL, { method: 'POST', body: estudiante });

// GET -> un estudiante del propio colegio (documento enmascarado; 404 si es de otro colegio)
export const obtenerEstudiante = (id) => peticion(`${URL}/${id}`);

// PUT -> actualiza nombre, apellido, grado y (opcional) documento; sin documento se conserva el actual
export const actualizarEstudiante = (id, estudiante) => peticion(`${URL}/${id}`, { method: 'PUT', body: estudiante });

// DELETE -> lo retira (borrado logico)
export const eliminarEstudiante = (id) => peticion(`${URL}/${id}`, { method: 'DELETE' });
