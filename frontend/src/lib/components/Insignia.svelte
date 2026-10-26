<script>
	// Estado de un evento o inscripcion con su color (clases .b y .<estado> de app.css). Reemplaza a Estado.svelte.
	let { valor } = $props();
	const NOMBRES = { borrador: 'Borrador', pendiente: 'Pendiente', publicado: 'Publicado', rechazado: 'Rechazado', cerrado: 'Cerrado', aceptada: 'Aceptada', rechazada: 'Rechazada' };
</script>

<span class="b {valor}">{NOMBRES[valor] ?? valor}</span>
