<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api.js';
	import { avisar } from '$lib/toast.svelte.js';

	let eventos = $state([]);
	let id = $state('');
	let grupos = $state([]);

	onMount(async () => {
		try {
			eventos = (await api('/organizador/eventos')).filter((e) => ['publicado', 'cerrado'].includes(e.estado));
			if (eventos[0]) {
				id = eventos[0].id;
				cargar();
			}
		} catch (e) {
			avisar(e.message, true);
		}
	});
	async function cargar() {
		grupos = id ? await api(`/organizador/eventos/${id}/asistencia`).catch((e) => (avisar(e.message, true), [])) : [];
	}
	async function guardar() {
		const marcas = grupos.flatMap((g) => g.estudiantes.map((s) => ({ id_inscripcion_estudiante: s.id_inscripcion_estudiante, asistio: s.asistio })));
		try {
			await api(`/organizador/eventos/${id}/asistencia`, { method: 'PUT', body: { marcas } });
			avisar('Asistencia guardada');
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>Asistencia | Conexión Escolar</title></svelte:head>

<h2>Asistencia</h2>
<p class="sub">Marca los estudiantes que asistieron. Solo aparecen colegios con inscripción aceptada.</p>
<div class="row">
	<label for="e" style="margin:0">Evento</label>
	<select id="e" bind:value={id} onchange={cargar}>
		{#each eventos as e}<option value={e.id}>{e.nombre}</option>{/each}
	</select>
	{#if grupos.length}<button class="btn" onclick={guardar}>Guardar asistencia</button>{/if}
</div>
{#each grupos as g}
	<div class="card" style="margin-bottom:12px">
		<h3>{g.colegio}</h3>
		{#each g.estudiantes as s}
			<label class="chk"><input type="checkbox" bind:checked={s.asistio} /> {s.nombre} <span class="mut">· grado {s.grado}</span></label>
		{/each}
	</div>
{:else}
	<p class="mut">{eventos.length ? 'Este evento aún no tiene colegios aceptados.' : 'No tienes eventos publicados.'}</p>
{/each}
