<script>
	import { onMount } from 'svelte';
	import { fechaLarga } from '$lib/services/api_base.js';
	import { listarEventos, decidirEvento, cerrarEvento } from '$lib/services/api_evento.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import Boton from '$lib/components/Boton.svelte';
	import Insignia from '$lib/components/Insignia.svelte';
	import SinDatos from '$lib/components/SinDatos.svelte';
	import { avisar } from '$lib/components/Mensaje.svelte';

	let eventos = $state([]);
	let filtro = $state('pendiente');
	let cargando = $state(true);

	async function cargar() {
		cargando = true;
		try {
			eventos = await listarEventos(filtro);
		} catch (e) {
			avisar(e.message, true);
		}
		cargando = false;
	}
	onMount(cargar);

	async function decidir(id, decision) {
		try {
			await decidirEvento(id, decision);
			avisar(decision === 'publicado' ? 'Evento publicado' : 'Evento rechazado');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
	async function cerrar(id) {
		try {
			await cerrarEvento(id);
			avisar('Evento cerrado');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>Eventos | Conexión Escolar</title></svelte:head>

<Header titulo="Eventos" subtitulo="Revisa y publica los eventos que envían los organizadores." />
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
<Card class="tabla">
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
					<td><Insignia valor={e.estado} /></td>
					<td>
						{#if e.estado === 'pendiente'}
							<Boton pequeno onclick={() => decidir(e.id, 'publicado')}>Publicar</Boton>
							<Boton variante="borrar" pequeno onclick={() => decidir(e.id, 'rechazado')}>Rechazar</Boton>
						{:else if e.estado === 'publicado'}
							<Boton variante="borde" pequeno onclick={() => cerrar(e.id)}>Cerrar</Boton>
						{/if}
					</td>
				</tr>
			{:else}
				<SinDatos texto={cargando ? 'Cargando…' : 'No hay eventos con este estado.'} columnas={7} />
			{/each}
		</tbody>
	</table>
</Card>
