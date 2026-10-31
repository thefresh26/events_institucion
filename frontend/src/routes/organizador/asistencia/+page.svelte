<script>
	import { onMount } from 'svelte';
	import { listarMisEventos } from '$lib/services/api_evento.js';
	import { obtenerAsistencia, guardarAsistencia } from '$lib/services/api_inscripcion.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import Boton from '$lib/components/Boton.svelte';
	import SinDatos from '$lib/components/SinDatos.svelte';
	import { avisar } from '$lib/components/Mensaje.svelte';

	let eventos = $state([]);
	let id = $state('');
	let grupos = $state([]);
	let cargando = $state(true);

	onMount(async () => {
		try {
			eventos = (await listarMisEventos()).filter((e) => ['publicado', 'cerrado'].includes(e.estado));
			if (eventos[0]) {
				id = eventos[0].id;
				await cargar();
			}
		} catch (e) {
			avisar(e.message, true);
		}
		cargando = false;
	});
	async function cargar() {
		grupos = id ? await obtenerAsistencia(id).catch((e) => (avisar(e.message, true), [])) : [];
	}
	async function guardar() {
		const marcas = grupos.flatMap((g) => g.estudiantes.map((s) => ({ id_inscripcion_estudiante: s.id_inscripcion_estudiante, asistio: s.asistio })));
		try {
			await guardarAsistencia(id, marcas);
			avisar('Asistencia guardada');
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>Asistencia | Conexión Escolar</title></svelte:head>

<Header titulo="Asistencia" subtitulo="Marca los estudiantes que asistieron. Solo aparecen colegios con inscripción aceptada." />
<div class="row">
	<label for="e" style="margin:0">Evento</label>
	<select id="e" bind:value={id} onchange={cargar}>
		{#each eventos as e}<option value={e.id}>{e.nombre}</option>{/each}
	</select>
	{#if grupos.length}<Boton onclick={guardar}>Guardar asistencia</Boton>{/if}
</div>
{#each grupos as g}
	<Card style="margin-bottom:12px">
		<h3>{g.colegio}</h3>
		{#each g.estudiantes as s}
			<label class="chk"><input type="checkbox" bind:checked={s.asistio} /> {s.nombre} <span class="mut">· grado {s.grado}</span></label>
		{/each}
	</Card>
{:else}
	{#if cargando}<p class="mut">Cargando...</p>{:else}<SinDatos texto={eventos.length ? 'Este evento aún no tiene colegios aceptados.' : 'No tienes eventos publicados.'} />{/if}
{/each}
