<script>
	// Enlaces al pie. Sin contenido muestra los de siempre; con contenido, los que la pagina ponga.
	let { children } = $props();
</script>

<p class="pie">
	{#if children}
		{@render children()}
	{:else}
		<a href="/politica-de-privacidad">Política de privacidad</a><a href="/terminos">Términos y condiciones</a>
	{/if}
</p>
