import { obtenerSesion, cerrarSesion } from '$lib/services/api_auth.js';

export const sesion = $state({ usuario: null, cargando: true });

export async function cargarSesion() {
	try {
		sesion.usuario = await obtenerSesion();
	} catch {
		sesion.usuario = null;
	}
	sesion.cargando = false;
}

export async function salir() {
	await cerrarSesion().catch(() => {});
	sesion.usuario = null;
}
