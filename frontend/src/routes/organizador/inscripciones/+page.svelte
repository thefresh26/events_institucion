<script>
	import { onMount } from 'svelte';
	import { fechaLarga } from '$lib/services/api_base.js';
	import { listarInscripciones, decidirInscripcion } from '$lib/services/api_inscripcion.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import Boton from '$lib/components/Boton.svelte';
	import Insignia from '$lib/components/Insignia.svelte';
	import TablaDatos from '$lib/components/TablaDatos.svelte';
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
	<TablaDatos
		filas={lista}
		vacio="Todavía no hay inscripciones."
		columnas={[
			{ t: 'Evento', k: 'evento' }, { t: 'Colegio', k: 'colegio' }, { t: 'Estudiantes', k: 'estudiantes' },
			{ t: 'Solicitada', k: 'creada_en' }, { t: 'Estado', k: 'estado' }, { t: '' }
		]}
	>
		{#snippet fila(i)}
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
		{/snippet}
	</TablaDatos>
</Card>
