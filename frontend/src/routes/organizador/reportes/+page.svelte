<script>
	import { onMount } from 'svelte';
	import { listarMisEventos } from '$lib/services/api_evento.js';
	import { urlReporteColegios, urlReporteEstudiantes } from '$lib/services/api_inscripcion.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import SinDatos from '$lib/components/SinDatos.svelte';
	import { avisar } from '$lib/components/Mensaje.svelte';

	let eventos = $state([]);
	let id = $state('');
	onMount(async () => {
		try {
			eventos = (await listarMisEventos()).filter((e) => ['publicado', 'cerrado'].includes(e.estado));
			id = eventos[0]?.id ?? '';
		} catch (e) {
			avisar(e.message, true);
		}
	});
</script>

<svelte:head><title>Reportes | Conexión Escolar</title></svelte:head>

<Header titulo="Reportes" subtitulo="Descarga listados en CSV (se abren en Excel)." />
<div class="row">
	<label for="e" style="margin:0">Evento</label>
	<select id="e" bind:value={id}>{#each eventos as e}<option value={e.id}>{e.nombre}</option>{/each}</select>
</div>
{#if id}
	<div class="grid g2">
		<Card><h3>Colegios inscritos</h3><p class="mut">Un colegio por fila, con su estado y cantidad de estudiantes.</p>
			<a class="btn" href={urlReporteColegios(id)} download>Descargar CSV</a></Card>
		<Card><h3>Estudiantes y asistencia</h3><p class="mut">Un estudiante por fila, de los colegios aceptados.</p>
			<a class="btn" href={urlReporteEstudiantes(id)} download>Descargar CSV</a></Card>
	</div>
	<p class="note">Estos listados contienen datos de menores de edad: úsalos solo para este evento. Cada descarga queda registrada.</p>
{:else}
	<SinDatos texto="No tienes eventos publicados." />
{/if}
