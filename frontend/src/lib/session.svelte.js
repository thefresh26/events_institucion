import { api } from '$lib/api.js';

export const sesion = $state({ usuario: null, cargando: true });

export async function cargarSesion() {
	try {
		sesion.usuario = await api('/auth/me');
	} catch {
		sesion.usuario = null;
	}
	sesion.cargando = false;
}

export async function salir() {
	await api('/auth/logout', { method: 'POST' }).catch(() => {});
	sesion.usuario = null;
}
