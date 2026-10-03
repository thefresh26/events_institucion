<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api.js';
	import { sesion } from '$lib/session.svelte.js';

	let tarjetas = $state([]);
	let eventos = $state([]);
	let error = $state('');
	const rol = sesion.usuario.rol;

	onMount(async () => {
		try {
			if (rol === 'administrador') {
				const r = await api('/admin/resumen');
				const e = r.eventos_por_estado;
				tarjetas = [['Eventos por aprobar', e.pendiente ?? 0], ['Eventos publicados', e.publicado ?? 0], ['Organizadores', r.organizadores], ['Colegios', r.colegios], ['Inscripciones', r.inscripciones]];
				if (r.organizadores_pendientes) tarjetas = [['Organizadores por aprobar', r.organizadores_pendientes], ...tarjetas];
				eventos = (await api('/admin/eventos?estado=publicado')).slice(0, 8);
			} else if (rol === 'organizador') {
				const [ev, ins] = await Promise.all([api('/organizador/eventos'), api('/organizador/inscripciones')]);
				eventos = ev.filter((x) => x.estado === 'publicado');
				tarjetas = [['Mis eventos', ev.length], ['Publicados', eventos.length], ['Inscripciones', ins.length], ['Por revisar', ins.filter((i) => i.estado === 'pendiente').length]];
			} else {
				const [ev, ins, es] = await Promise.all([api('/colegio/eventos'), api('/colegio/inscripciones'), api('/colegio/estudiantes')]);
				eventos = ev;
				tarjetas = [['Eventos abiertos', ev.length], ['Mis inscripciones', ins.length], ['Aceptadas', ins.filter((i) => i.estado === 'aceptada').length], ['Mis estudiantes', es.length]];
			}
		} catch (e) {
			error = e.message;
		}
	});
</script>

<svelte:head><title>Panel | Eventos Escolares</title></svelte:head>

<h2>Panel</h2>
<p class="sub">Hola, {sesion.usuario.nombre}.</p>
{#if error}<p class="err" role="alert">{error}</p>{/if}
<div class="grid g4">
	{#each tarjetas as [nombre, valor]}
		<div class="card m"><span>{nombre}</span><b>{valor}</b></div>
	{/each}
</div>
<div class="card" style="margin-top:14px">
	<h3>Ocupación de cupos de los eventos publicados</h3>
	{#each eventos as e}
		<div class="hb">
			<span>{e.nombre}<b>{e.colegios_inscritos} / {e.cupo_colegios} colegios</b></span>
			<div><i style="width:{Math.min(100, (e.colegios_inscritos / e.cupo_colegios) * 100)}%"></i></div>
		</div>
	{:else}
		<p class="mut">Todavía no hay eventos publicados.</p>
	{/each}
</div>
