<script>
	// Tarjeta blanca (oscura en modo oscuro) de app.css; lo que va dentro llega como contenido (children = slot).
	// class: clases extra (ej. "m" = tarjeta de metrica); lo demas (style, role...) pasa directo al <div>.
	let { children, class: clase = '', ...resto } = $props();
</script>

<div class="card {clase}" {...resto}>
	{@render children?.()}
</div>
