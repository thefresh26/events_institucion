import { peticion } from './api_base.js';

// Listas para los formularios (solo registros con estado = true)

// GET /catalogos/ciudades -> [{ id, nombre, departamento }]
export const listarCiudades = () => peticion('/catalogos/ciudades');

// GET /catalogos/grados -> [{ id, nombre }]
export const listarGrados = () => peticion('/catalogos/grados');

// GET /catalogos/categorias -> [{ id, nombre }]
export const listarCategorias = () => peticion('/catalogos/categorias');
