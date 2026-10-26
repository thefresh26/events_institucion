<script>
	import { onMount } from 'svelte';
	import { listarColegios } from '$lib/services/api_admin.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import Insignia from '$lib/components/Insignia.svelte';
	import SinDatos from '$lib/components/SinDatos.svelte';
	import { avisar } from '$lib/components/Mensaje.svelte';

	let lista = $state([]);
	onMount(async () => {
		try {
			lista = await listarColegios();
		} catch (e) {
			avisar(e.message, true);
		}
	});
</script>

<svelte:head><title>Colegios | Conexión Escolar</title></svelte:head>

<Header titulo="Colegios" subtitulo="Colegios registrados por los organizadores." />
<Card class="tabla">
	<table>
		<thead><tr><th>Colegio</th><th>NIT</th><th>Ciudad</th><th>Organizador</th><th>Estado</th></tr></thead>
		<tbody>
			{#each lista as c}
				<tr><td><strong>{c.nombre}</strong></td><td>{c.nit}</td><td>{c.ciudad}</td><td>{c.organizador}</td>
					<td><Insignia valor={c.activo ? 'publicado' : 'borrador'} texto={c.activo ? 'Activo' : 'Inactivo'} /></td></tr>
			{:else}
				<SinDatos texto="Aún no hay colegios." columnas={5} />
			{/each}
		</tbody>
	</table>
</Card>
