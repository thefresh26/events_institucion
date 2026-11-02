import { peticion } from './api_base.js';

const URL = '/estudiantes';

// GET -> estudiantes del colegio que inicio sesion
export const listarEstudiantes = () => peticion(URL);

// POST -> registra un estudiante (con la autorizacion del acudiente)
export const crearEstudiante = (estudiante) => peticion(URL, { method: 'POST', body: estudiante });

// GET -> un estudiante del propio colegio (404 si es de otro colegio)
export const obtenerEstudiante = (id) => peticion(`${URL}/${id}`);

// PUT -> actualiza nombre, apellido y grado
export const actualizarEstudiante = (id, estudiante) => peticion(`${URL}/${id}`, { method: 'PUT', body: estudiante });

// DELETE -> lo retira (borrado logico)
export const eliminarEstudiante = (id) => peticion(`${URL}/${id}`, { method: 'DELETE' });
