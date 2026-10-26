<script>
	// Estado de un evento o inscripcion con su color (clases .b y .<estado> de app.css). Reemplaza a Estado.svelte.
	// texto: opcional, para usar el color de un estado con otro nombre (ej. valor="publicado" texto="Activo").
	let { valor, texto = '' } = $props();
	const NOMBRES = { borrador: 'Borrador', pendiente: 'Pendiente', publicado: 'Publicado', rechazado: 'Rechazado', cerrado: 'Cerrado', aceptada: 'Aceptada', rechazada: 'Rechazada' };
</script>

<span class="b {valor}">{texto || (NOMBRES[valor] ?? valor)}</span>
