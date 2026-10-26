<script>
	import { onMount } from 'svelte';
	import { fechaLarga } from '$lib/services/api_base.js';
	import { listarEventosDisponibles } from '$lib/services/api_evento.js';
	import { listarEstudiantes } from '$lib/services/api_estudiante.js';
	import { inscribirse } from '$lib/services/api_inscripcion.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import Boton from '$lib/components/Boton.svelte';
	import Insignia from '$lib/components/Insignia.svelte';
	import SinDatos from '$lib/components/SinDatos.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import { avisar } from '$lib/components/Mensaje.svelte';

	let eventos = $state([]);
	let estudiantes = $state([]);
	let sel = $state(null); // evento al que nos vamos a inscribir
	let marcados = $state([]);
	let error = $state('');

	async function cargar() {
		try {
			[eventos, estudiantes] = await Promise.all([listarEventosDisponibles(), listarEstudiantes()]);
		} catch (e) {
			avisar(e.message, true);
		}
	}
	onMount(cargar);

	function abrir(e) {
		error = '';
		marcados = [];
		sel = e;
	}
	async function inscribir(ev) {
		ev.preventDefault();
		error = '';
		if (marcados.length > sel.cupo_estudiantes) return (error = `Máximo ${sel.cupo_estudiantes} estudiantes`);
		try {
			await inscribirse(sel.id, marcados);
			sel = null;
			avisar('Inscripción enviada. El organizador la revisará.');
			cargar();
		} catch (e) {
			error = e.message;
		}
	}
</script>

<svelte:head><title>Eventos | Conexión Escolar</title></svelte:head>

<Header titulo="Eventos disponibles" subtitulo="Eventos publicados por tu organizador. Matricula a tu colegio eligiendo a los estudiantes que participarán." />
<div class="grid g2">
	{#each eventos as e}
		<Card>
			<h3>{e.nombre}</h3>
			<p class="mut" style="margin:0 0 8px">{e.descripcion ?? ''}</p>
			<p style="margin:0 0 4px">{fechaLarga(e.fecha_inicio)} · {e.lugar}</p>
			<p class="mut" style="margin:0 0 12px">Cupos: {e.colegios_inscritos}/{e.cupo_colegios} colegios · hasta {e.cupo_estudiantes} estudiantes por colegio</p>
			{#if e.mi_inscripcion}
				<Insignia valor={e.mi_inscripcion} />
			{:else}
				<Boton disabled={e.colegios_inscritos >= e.cupo_colegios} onclick={() => abrir(e)}>
					{e.colegios_inscritos >= e.cupo_colegios ? 'Sin cupos' : 'Matricular colegio'}
				</Boton>
			{/if}
		</Card>
	{:else}
		<SinDatos texto="No hay eventos publicados por ahora." />
	{/each}
</div>

{#if sel}
	<Modal titulo={`Matricular en ${sel.nombre}`} cerrar={() => (sel = null)}>
		<form onsubmit={inscribir}>
			<p class="mut">Elige hasta {sel.cupo_estudiantes} estudiantes. Llevas {marcados.length}.</p>
			{#each estudiantes as s}
				<label class="chk"><input type="checkbox" value={s.id} bind:group={marcados} /> {s.nombre} {s.apellido} <span class="mut">· grado {s.grado}</span></label>
			{:else}
				<SinDatos texto="Primero registra estudiantes en la sección «Estudiantes»." />
			{/each}
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<div class="row" style="justify-content:flex-end;margin:16px 0 0">
				<Boton variante="borde" onclick={() => (sel = null)}>Cancelar</Boton>
				<Boton tipo="submit" disabled={!marcados.length}>Enviar inscripción</Boton>
			</div>
		</form>
	</Modal>
{/if}
