<script>
	import { onMount } from 'svelte';
	import { fechaLarga } from '$lib/services/api_base.js';
	import { listarInscripciones, decidirInscripcion } from '$lib/services/api_inscripcion.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import Boton from '$lib/components/Boton.svelte';
	import Insignia from '$lib/components/Insignia.svelte';
	import SinDatos from '$lib/components/SinDatos.svelte';
	import { avisar } from '$lib/components/Mensaje.svelte';

	let lista = $state([]);
	async function cargar() {
		try {
			lista = await listarInscripciones();
		} catch (e) {
			avisar(e.message, true);
		}
	}
	onMount(cargar);

	async function decidir(id, estado) {
		try {
			await decidirInscripcion(id, estado);
			avisar(estado === 'aceptada' ? 'Inscripción aceptada' : 'Inscripción rechazada');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>Inscripciones | Conexión Escolar</title></svelte:head>

<Header titulo="Inscripciones" subtitulo="Colegios que quieren participar en tus eventos." />
<Card class="tabla">
	<table>
		<thead><tr><th>Evento</th><th>Colegio</th><th>Estudiantes</th><th>Solicitada</th><th>Estado</th><th></th></tr></thead>
		<tbody>
			{#each lista as i}
				<tr>
					<td><strong>{i.evento}</strong></td><td>{i.colegio}</td><td>{i.estudiantes}</td><td>{fechaLarga(i.creada_en)}</td>
					<td><Insignia valor={i.estado} /></td>
					<td>
						{#if i.estado === 'pendiente'}
							<Boton pequeno onclick={() => decidir(i.id, 'aceptada')}>Aceptar</Boton>
							<Boton variante="borrar" pequeno onclick={() => decidir(i.id, 'rechazada')}>Rechazar</Boton>
						{/if}
					</td>
				</tr>
			{:else}
				<SinDatos texto="Todavía no hay inscripciones." columnas={6} />
			{/each}
		</tbody>
	</table>
</Card>
