<script>
	// variante: primario | borde | borrar  ·  pequeno: boton compacto (tablas)
	let { variante = 'primario', tipo = 'button', pequeno = false, disabled = false, onclick, children } = $props();
</script>

<button type={tipo} class="btn" class:o={variante === 'borde'} class:r={variante === 'borrar'} class:s={pequeno} {disabled} {onclick}>
	{@render children?.()}
</button>
