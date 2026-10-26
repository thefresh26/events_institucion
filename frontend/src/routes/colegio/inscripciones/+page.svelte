<script>
	import { onMount } from 'svelte';
	import { fechaLarga } from '$lib/services/api_base.js';
	import { listarMisInscripciones } from '$lib/services/api_inscripcion.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import Insignia from '$lib/components/Insignia.svelte';
	import SinDatos from '$lib/components/SinDatos.svelte';
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
	<table>
		<thead><tr><th>Evento</th><th>Fecha</th><th>Estudiantes</th><th>Estado</th></tr></thead>
		<tbody>
			{#each lista as i}
				<tr><td><strong>{i.evento}</strong></td><td>{fechaLarga(i.fecha_inicio)}</td><td>{i.estudiantes.join(', ')}</td><td><Insignia valor={i.estado} /></td></tr>
			{:else}
				<SinDatos texto="Aún no tienes inscripciones." columnas={4} />
			{/each}
		</tbody>
	</table>
</Card>
