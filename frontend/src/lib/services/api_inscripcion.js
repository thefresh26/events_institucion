import { peticion, URL_BASE } from './api_base.js';

// ---------------- Colegio ----------------
// POST -> inscribe estudiantes (lista de ids) en un evento
export const inscribirse = (idEvento, estudiantes) =>
	peticion(`/colegio/eventos/${idEvento}/inscripcion`, { method: 'POST', body: { estudiantes } });

// GET -> inscripciones del colegio que inicio sesion
export const listarMisInscripciones = () => peticion('/colegio/inscripciones');

// ---------------- Organizador ----------------
// GET -> inscripciones a los eventos del organizador
export const listarInscripciones = () => peticion('/organizador/inscripciones');

// PATCH -> estado: 'aceptada' o 'rechazada'
export const decidirInscripcion = (id, estado) => peticion(`/organizador/inscripciones/${id}`, { method: 'PATCH', body: { estado } });

// GET -> estudiantes aceptados del evento, agrupados por colegio
export const obtenerAsistencia = (idEvento) => peticion(`/organizador/eventos/${idEvento}/asistencia`);

// PUT -> marcas: [{ id_inscripcion_estudiante, asistio }]
export const guardarAsistencia = (idEvento, marcas) =>
	peticion(`/organizador/eventos/${idEvento}/asistencia`, { method: 'PUT', body: { marcas } });

// Reportes CSV: se descargan con un enlace <a href={...} download>, por eso se devuelve la URL y no los datos
export const urlReporteColegios = (idEvento) => `${URL_BASE}/organizador/eventos/${idEvento}/reporte/colegios.csv`;
export const urlReporteEstudiantes = (idEvento) => `${URL_BASE}/organizador/eventos/${idEvento}/reporte/estudiantes.csv`;
