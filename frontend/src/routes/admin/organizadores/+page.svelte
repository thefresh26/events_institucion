<script>
	import { onMount } from 'svelte';
	import { listarOrganizadores, activarOrganizador } from '$lib/services/api_admin.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import Boton from '$lib/components/Boton.svelte';
	import Insignia from '$lib/components/Insignia.svelte';
	import SinDatos from '$lib/components/SinDatos.svelte';
	import { avisar } from '$lib/components/Mensaje.svelte';

	let lista = $state([]);
	async function cargar() {
		try {
			lista = await listarOrganizadores();
		} catch (e) {
			avisar(e.message, true);
		}
	}
	onMount(cargar);

	async function activar(o, activo) {
		try {
			await activarOrganizador(o.id, activo);
			avisar(activo ? 'Organizador aprobado' : 'Organizador desactivado');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>Organizadores | Conexión Escolar</title></svelte:head>

<Header titulo="Organizadores" subtitulo="Aprueba las cuentas nuevas antes de que puedan crear eventos." />
<Card class="tabla">
	<table>
		<thead><tr><th>Organización</th><th>NIT</th><th>Correo</th><th>Teléfono</th><th>Estado</th><th></th></tr></thead>
		<tbody>
			{#each lista as o}
				<tr>
					<td><strong>{o.nombre}</strong></td><td>{o.nit}</td><td>{o.correo}</td><td>{o.telefono ?? ''}</td>
					<td><Insignia valor={o.activo ? 'publicado' : 'pendiente'} texto={o.activo ? 'Activo' : 'Pendiente / inactivo'} /></td>
					<td>
						{#if o.activo}
							<Boton variante="borde" pequeno onclick={() => activar(o, false)}>Desactivar</Boton>
						{:else}
							<Boton pequeno onclick={() => activar(o, true)}>Aprobar</Boton>
						{/if}
					</td>
				</tr>
			{:else}
				<SinDatos texto="Aún no hay organizadores registrados." columnas={6} />
			{/each}
		</tbody>
	</table>
</Card>
