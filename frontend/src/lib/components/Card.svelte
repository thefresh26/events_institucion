<script>
	// Tarjeta blanca (oscura en modo oscuro) de app.css; lo que va dentro llega como contenido (children = slot).
	let { children } = $props();
</script>

<div class="card">
	{@render children?.()}
</div>
