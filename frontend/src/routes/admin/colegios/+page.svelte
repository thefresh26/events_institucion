<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api.js';
	import { avisar } from '$lib/toast.svelte.js';

	let lista = $state([]);
	onMount(async () => {
		try {
			lista = await api('/admin/colegios');
		} catch (e) {
			avisar(e.message, true);
		}
	});
</script>

<svelte:head><title>Colegios | Eventos Escolares</title></svelte:head>

<h2>Colegios</h2>
<p class="sub">Colegios registrados por los organizadores.</p>
<div class="card tabla">
	<table>
		<thead><tr><th>Colegio</th><th>NIT</th><th>Ciudad</th><th>Organizador</th><th>Estado</th></tr></thead>
		<tbody>
			{#each lista as c}
				<tr><td><strong>{c.nombre}</strong></td><td>{c.nit}</td><td>{c.ciudad}</td><td>{c.organizador}</td>
					<td><span class="b {c.activo ? 'publicado' : 'borrador'}">{c.activo ? 'Activo' : 'Inactivo'}</span></td></tr>
			{:else}
				<tr><td colspan="5" class="mut">Aún no hay colegios.</td></tr>
			{/each}
		</tbody>
	</table>
</div>
