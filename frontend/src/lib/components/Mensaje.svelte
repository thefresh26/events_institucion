<script module>
	// Aviso flotante. Cualquier pagina hace  import { avisar } from '$lib/components/Mensaje.svelte'
	// y llama avisar('Guardado') o avisar('Algo falló', true). El +layout pone <Mensaje /> una sola vez.
	const aviso = $state({ texto: '', error: false });
	let reloj;

	export function avisar(texto, error = false) {
		aviso.texto = texto;
		aviso.error = error;
		clearTimeout(reloj);
		reloj = setTimeout(() => (aviso.texto = ''), 3500);
	}
</script>

{#if aviso.texto}
	<div class="toast" class:error={aviso.error} role="status">{aviso.texto}</div>
{/if}
