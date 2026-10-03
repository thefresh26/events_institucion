<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api.js';
	import { avisar } from '$lib/toast.svelte.js';

	let eventos = $state([]);
	let id = $state('');
	onMount(async () => {
		try {
			eventos = (await api('/organizador/eventos')).filter((e) => ['publicado', 'cerrado'].includes(e.estado));
			id = eventos[0]?.id ?? '';
		} catch (e) {
			avisar(e.message, true);
		}
	});
</script>

<svelte:head><title>Reportes | Eventos Escolares</title></svelte:head>

<h2>Reportes</h2>
<p class="sub">Descarga listados en CSV (se abren en Excel).</p>
<div class="row">
	<label for="e" style="margin:0">Evento</label>
	<select id="e" bind:value={id}>{#each eventos as e}<option value={e.id}>{e.nombre}</option>{/each}</select>
</div>
{#if id}
	<div class="grid g2">
		<div class="card"><h3>Colegios inscritos</h3><p class="mut">Un colegio por fila, con su estado y cantidad de estudiantes.</p>
			<a class="btn" href="/api/v1/organizador/eventos/{id}/reporte/colegios.csv" download>Descargar CSV</a></div>
		<div class="card"><h3>Estudiantes y asistencia</h3><p class="mut">Un estudiante por fila, de los colegios aceptados.</p>
			<a class="btn" href="/api/v1/organizador/eventos/{id}/reporte/estudiantes.csv" download>Descargar CSV</a></div>
	</div>
	<p class="note">Estos listados contienen datos de menores de edad: úsalos solo para este evento. Cada descarga queda registrada.</p>
{:else}
	<p class="mut">No tienes eventos publicados.</p>
{/if}
