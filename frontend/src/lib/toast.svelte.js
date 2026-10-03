export const aviso = $state({ texto: '', error: false });
let t;
export function avisar(texto, error = false) {
	aviso.texto = texto;
	aviso.error = error;
	clearTimeout(t);
	t = setTimeout(() => (aviso.texto = ''), 3500);
}
