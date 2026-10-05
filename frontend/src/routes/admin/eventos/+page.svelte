<script>
	import { onMount } from 'svelte';
	import { api, fechaLarga } from '$lib/api.js';
	import Estado from '$lib/Estado.svelte';
	import { avisar } from '$lib/toast.svelte.js';

	let eventos = $state([]);
	let filtro = $state('pendiente');
	let cargando = $state(true);

	async function cargar() {
		cargando = true;
		try {
			eventos = await api('/admin/eventos' + (filtro ? `?estado=${filtro}` : ''));
		} catch (e) {
			avisar(e.message, true);
		}
		cargando = false;
	}
	onMount(cargar);

	async function decidir(id, decision) {
		try {
			await api(`/admin/eventos/${id}/decision`, { method: 'PATCH', body: { decision } });
			avisar(decision === 'publicado' ? 'Evento publicado' : 'Evento rechazado');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
	async function cerrar(id) {
		try {
			await api(`/admin/eventos/${id}/cerrar`, { method: 'POST' });
			avisar('Evento cerrado');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>Eventos | Conexión Escolar</title></svelte:head>

<h2>Eventos</h2>
<p class="sub">Revisa y publica los eventos que envían los organizadores.</p>
<div class="row">
	<label for="f" style="margin:0">Estado</label>
	<select id="f" bind:value={filtro} onchange={cargar}>
		<option value="pendiente">Pendientes de aprobación</option>
		<option value="publicado">Publicados</option>
		<option value="rechazado">Rechazados</option>
		<option value="cerrado">Cerrados</option>
		<option value="">Todos</option>
	</select>
</div>
<div class="card tabla">
	<table>
		<thead><tr><th>Evento</th><th>Organizador</th><th>Fecha</th><th>Lugar</th><th>Cupos</th><th>Estado</th><th></th></tr></thead>
		<tbody>
			{#each eventos as e}
				<tr>
					<td><strong>{e.nombre}</strong><br /><span class="mut">{e.categoria}</span></td>
					<td>{e.organizador}</td>
					<td>{fechaLarga(e.fecha_inicio)}</td>
					<td>{e.lugar}</td>
					<td>{e.colegios_inscritos}/{e.cupo_colegios}</td>
					<td><Estado valor={e.estado} /></td>
					<td>
						{#if e.estado === 'pendiente'}
							<button class="btn s" onclick={() => decidir(e.id, 'publicado')}>Publicar</button>
							<button class="btn r s" onclick={() => decidir(e.id, 'rechazado')}>Rechazar</button>
						{:else if e.estado === 'publicado'}
							<button class="btn o s" onclick={() => cerrar(e.id)}>Cerrar</button>
						{/if}
					</td>
				</tr>
			{:else}
				<tr><td colspan="7" class="mut">{cargando ? 'Cargando…' : 'No hay eventos con este estado.'}</td></tr>
			{/each}
		</tbody>
	</table>
</div>
