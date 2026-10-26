// Base de todos los services (api_<modulo>.js): aqui esta el UNICO fetch del frontend.
// La sesion viaja en una cookie HttpOnly: el JavaScript no maneja ni ve ningun token.
// Si la sesion vencio, el servidor responde 401 y llega aqui como ApiError con estado 401.
export const URL_BASE = '/api/v1';

export class ApiError extends Error {
	constructor(mensaje, estado) {
		super(mensaje);
		this.estado = estado;
	}
}

function mensajeDe(datos, estado) {
	const d = datos?.detail;
	if (typeof d === 'string') return d;
	if (Array.isArray(d) && d.length) {
		const campo = String(d[0].loc?.[d[0].loc.length - 1] ?? '');
		return `${campo ? campo + ': ' : ''}${String(d[0].msg ?? 'dato inválido').replace('Value error, ', '')}`;
	}
	return estado === 429 ? 'Demasiados intentos, espera un momento' : 'Ocurrió un error. Intenta de nuevo.';
}

export async function peticion(ruta, { method = 'GET', body } = {}) {
	let r;
	try {
		r = await fetch(URL_BASE + ruta, {
			method,
			credentials: 'same-origin',
			headers: body ? { 'Content-Type': 'application/json' } : {},
			body: body ? JSON.stringify(body) : undefined
		});
	} catch {
		throw new ApiError('No hay conexión con el servidor. Revisa tu internet.', 0);
	}
	if (r.status === 204) return null;
	const datos = await r.json().catch(() => null);
	if (!r.ok) throw new ApiError(mensajeDe(datos, r.status), r.status);
	return datos;
}

// Formato de las fechas que devuelve la API (ej. "15 nov 2026, 3:50 p. m.")
export const fechaLarga = (iso) =>
	iso ? new Date(iso).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' }) : '';
