<script>
	import { onMount } from 'svelte';
	import { sesion } from '$lib/session.svelte.js';
	import { obtenerResumen } from '$lib/services/api_admin.js';
	import { listarEventos, listarMisEventos, listarEventosDisponibles } from '$lib/services/api_evento.js';
	import { listarInscripciones, listarMisInscripciones } from '$lib/services/api_inscripcion.js';
	import { listarEstudiantes } from '$lib/services/api_estudiante.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import SinDatos from '$lib/components/SinDatos.svelte';

	let tarjetas = $state([]);
	let eventos = $state([]);
	let error = $state('');
	const rol = sesion.usuario.rol;

	onMount(async () => {
		try {
			if (rol === 'administrador') {
				const r = await obtenerResumen();
				const e = r.eventos_por_estado;
				tarjetas = [['Eventos por aprobar', e.pendiente ?? 0], ['Eventos publicados', e.publicado ?? 0], ['Organizadores', r.organizadores], ['Colegios', r.colegios], ['Inscripciones', r.inscripciones]];
				if (r.organizadores_pendientes) tarjetas = [['Organizadores por aprobar', r.organizadores_pendientes], ...tarjetas];
				eventos = (await listarEventos('publicado')).slice(0, 8);
			} else if (rol === 'organizador') {
				const [ev, ins] = await Promise.all([listarMisEventos(), listarInscripciones()]);
				eventos = ev.filter((x) => x.estado === 'publicado');
				tarjetas = [['Mis eventos', ev.length], ['Publicados', eventos.length], ['Inscripciones', ins.length], ['Por revisar', ins.filter((i) => i.estado === 'pendiente').length]];
			} else {
				const [ev, ins, es] = await Promise.all([listarEventosDisponibles(), listarMisInscripciones(), listarEstudiantes()]);
				eventos = ev;
				tarjetas = [['Eventos abiertos', ev.length], ['Mis inscripciones', ins.length], ['Aceptadas', ins.filter((i) => i.estado === 'aceptada').length], ['Mis estudiantes', es.length]];
			}
		} catch (e) {
			error = e.message;
		}
	});
</script>

<svelte:head><title>Panel | Conexión Escolar</title></svelte:head>

<Header titulo="Panel" subtitulo="Hola, {sesion.usuario.nombre}. Este es el resumen de hoy." />
{#if error}<p class="err" role="alert">{error}</p>{/if}
<div class="grid g4">
	{#each tarjetas as [nombre, valor]}
		<Card class="m"><span>{nombre}</span><b>{valor}</b></Card>
	{/each}
</div>
<Card style="margin-top:14px">
	<h3>Ocupación de cupos de los eventos publicados</h3>
	{#each eventos as e}
		<div class="hb">
			<span>{e.nombre}<b>{e.colegios_inscritos} / {e.cupo_colegios} colegios</b></span>
			<div><i style="width:{Math.min(100, (e.colegios_inscritos / e.cupo_colegios) * 100)}%"></i></div>
		</div>
	{:else}
		<SinDatos texto="Todavía no hay eventos publicados." />
	{/each}
</Card>
