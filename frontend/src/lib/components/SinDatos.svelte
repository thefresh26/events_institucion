<script>
	// Aviso de lista vacia. Con "columnas" se dibuja como fila de tabla (ocupa todo el ancho).
	let { texto = 'No hay datos para mostrar.', columnas = 0 } = $props();
</script>

{#if columnas}
	<tr><td colspan={columnas} class="mut">{texto}</td></tr>
{:else}
	<p class="mut">{texto}</p>
{/if}
