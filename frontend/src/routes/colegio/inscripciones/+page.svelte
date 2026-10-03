<script>
	import { onMount } from 'svelte';
	import { api, fechaLarga } from '$lib/api.js';
	import Estado from '$lib/Estado.svelte';
	import { avisar } from '$lib/toast.svelte.js';

	let lista = $state([]);
	onMount(async () => {
		try {
			lista = await api('/colegio/inscripciones');
		} catch (e) {
			avisar(e.message, true);
		}
	});
</script>

<svelte:head><title>Mis inscripciones | Eventos Escolares</title></svelte:head>

<h2>Mis inscripciones</h2>
<p class="sub">Estado de tu colegio en cada evento.</p>
<div class="card tabla">
	<table>
		<thead><tr><th>Evento</th><th>Fecha</th><th>Estudiantes</th><th>Estado</th></tr></thead>
		<tbody>
			{#each lista as i}
				<tr><td><strong>{i.evento}</strong></td><td>{fechaLarga(i.fecha_inicio)}</td><td>{i.estudiantes.join(', ')}</td><td><Estado valor={i.estado} /></td></tr>
			{:else}
				<tr><td colspan="4" class="mut">Aún no tienes inscripciones.</td></tr>
			{/each}
		</tbody>
	</table>
</div>
