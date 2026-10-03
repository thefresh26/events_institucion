<script>
	let { valor } = $props();
	const ROT = { borrador: 'Borrador', pendiente: 'Pendiente', publicado: 'Publicado', rechazado: 'Rechazado', cerrado: 'Cerrado', aceptada: 'Aceptada', rechazada: 'Rechazada' };
</script>

<span class="b {valor}">{ROT[valor] ?? valor}</span>
