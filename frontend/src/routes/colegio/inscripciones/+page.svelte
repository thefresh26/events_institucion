<script>
	import { onMount } from 'svelte';
	import { fechaLarga } from '$lib/services/api_base.js';
	import { listarMisInscripciones } from '$lib/services/api_inscripcion.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import Insignia from '$lib/components/Insignia.svelte';
	import TablaDatos from '$lib/components/TablaDatos.svelte';
	import { avisar } from '$lib/components/Mensaje.svelte';

	let lista = $state([]);
	onMount(async () => {
		try {
			lista = await listarMisInscripciones();
		} catch (e) {
			avisar(e.message, true);
		}
	});
</script>

<svelte:head><title>Mis inscripciones | Conexión Escolar</title></svelte:head>

<Header titulo="Mis inscripciones" subtitulo="Estado de tu colegio en cada evento." />
<Card class="tabla">
	<TablaDatos
		filas={lista}
		vacio="Aún no tienes inscripciones."
		columnas={[{ t: 'Evento', k: 'evento' }, { t: 'Fecha', k: 'fecha_inicio' }, { t: 'Estudiantes', k: (i) => i.estudiantes.length }, { t: 'Estado', k: 'estado' }]}
	>
		{#snippet fila(i)}
			<tr><td><strong>{i.evento}</strong></td><td>{fechaLarga(i.fecha_inicio)}</td><td>{i.estudiantes.join(', ')}</td><td><Insignia valor={i.estado} /></td></tr>
		{/snippet}
	</TablaDatos>
</Card>
