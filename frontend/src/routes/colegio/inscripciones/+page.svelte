<script>
	import { onMount } from 'svelte';
	import { fechaLarga } from '$lib/services/api_base.js';
	import { listarMisInscripciones, cancelarInscripcion } from '$lib/services/api_inscripcion.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import Insignia from '$lib/components/Insignia.svelte';
	import Boton from '$lib/components/Boton.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import TablaDatos from '$lib/components/TablaDatos.svelte';
	import { avisar } from '$lib/components/Mensaje.svelte';

	let lista = $state([]);
	let porCancelar = $state(null);
	async function cargar() {
		try {
			lista = await listarMisInscripciones();
		} catch (e) {
			avisar(e.message, true);
		}
	}
	onMount(cargar);

	async function cancelar() {
		const i = porCancelar;
		porCancelar = null;
		try {
			await cancelarInscripcion(i.id);
			avisar('Inscripción cancelada');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>Mis inscripciones | Conexión Escolar</title></svelte:head>

<Header titulo="Mis inscripciones" subtitulo="Estado de tu colegio en cada evento." />
<Card class="tabla">
	<TablaDatos
		filas={lista}
		vacio="Aún no tienes inscripciones."
		columnas={[{ t: 'Evento', k: 'evento' }, { t: 'Fecha', k: 'fecha_inicio' }, { t: 'Estudiantes', k: (i) => i.estudiantes.length }, { t: 'Estado', k: 'estado' }, { t: '' }]}
	>
		{#snippet fila(i)}
			<tr><td><strong>{i.evento}</strong></td><td>{fechaLarga(i.fecha_inicio)}</td><td>{i.estudiantes.join(', ')}</td><td><Insignia valor={i.estado} /></td><td>{#if i.estado === 'pendiente'}<Boton variante="borrar" pequeno onclick={() => (porCancelar = i)}>Cancelar</Boton>{/if}</td></tr>
		{/snippet}
	</TablaDatos>
</Card>

{#if porCancelar}
	<Modal titulo="Cancelar inscripción" cerrar={() => (porCancelar = null)}>
		<p>¿Cancelar la inscripción a <strong>{porCancelar.evento}</strong>? Solo se puede mientras el organizador no la haya decidido.</p>
		<div class="row" style="justify-content:flex-end;margin:16px 0 0">
			<Boton variante="borde" onclick={() => (porCancelar = null)}>Volver</Boton><Boton variante="borrar" onclick={cancelar}>Cancelar inscripción</Boton>
		</div>
	</Modal>
{/if}
