<script>
	import { onMount } from 'svelte';
	import { api, fechaLarga } from '$lib/api.js';
	import Estado from '$lib/Estado.svelte';
	import { avisar } from '$lib/toast.svelte.js';

	let lista = $state([]);
	async function cargar() {
		try {
			lista = await api('/organizador/inscripciones');
		} catch (e) {
			avisar(e.message, true);
		}
	}
	onMount(cargar);

	async function decidir(id, estado) {
		try {
			await api(`/organizador/inscripciones/${id}`, { method: 'PATCH', body: { estado } });
			avisar(estado === 'aceptada' ? 'Inscripción aceptada' : 'Inscripción rechazada');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>Inscripciones | Eventos Escolares</title></svelte:head>

<h2>Inscripciones</h2>
<p class="sub">Colegios que quieren participar en tus eventos.</p>
<div class="card tabla">
	<table>
		<thead><tr><th>Evento</th><th>Colegio</th><th>Estudiantes</th><th>Solicitada</th><th>Estado</th><th></th></tr></thead>
		<tbody>
			{#each lista as i}
				<tr>
					<td><strong>{i.evento}</strong></td><td>{i.colegio}</td><td>{i.estudiantes}</td><td>{fechaLarga(i.creada_en)}</td>
					<td><Estado valor={i.estado} /></td>
					<td>
						{#if i.estado === 'pendiente'}
							<button class="btn s" onclick={() => decidir(i.id, 'aceptada')}>Aceptar</button>
							<button class="btn r s" onclick={() => decidir(i.id, 'rechazada')}>Rechazar</button>
						{/if}
					</td>
				</tr>
			{:else}
				<tr><td colspan="6" class="mut">Todavía no hay inscripciones.</td></tr>
			{/each}
		</tbody>
	</table>
</div>
