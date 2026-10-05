<script>
	import { onMount } from 'svelte';
	import { api, fechaLarga } from '$lib/api.js';
	import Estado from '$lib/Estado.svelte';
	import Modal from '$lib/Modal.svelte';
	import { avisar } from '$lib/toast.svelte.js';

	let eventos = $state([]);
	let estudiantes = $state([]);
	let sel = $state(null); // evento al que nos vamos a inscribir
	let marcados = $state([]);
	let error = $state('');

	async function cargar() {
		try {
			[eventos, estudiantes] = await Promise.all([api('/colegio/eventos'), api('/colegio/estudiantes')]);
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
			await api(`/colegio/eventos/${sel.id}/inscripcion`, { method: 'POST', body: { estudiantes: marcados } });
			sel = null;
			avisar('Inscripción enviada. El organizador la revisará.');
			cargar();
		} catch (e) {
			error = e.message;
		}
	}
</script>

<svelte:head><title>Eventos | Conexión Escolar</title></svelte:head>

<h2>Eventos disponibles</h2>
<p class="sub">Eventos publicados por tu organizador. Matricula a tu colegio eligiendo a los estudiantes que participarán.</p>
<div class="grid g2">
	{#each eventos as e}
		<div class="card">
			<h3>{e.nombre}</h3>
			<p class="mut" style="margin:0 0 8px">{e.descripcion ?? ''}</p>
			<p style="margin:0 0 4px">{fechaLarga(e.fecha_inicio)} · {e.lugar}</p>
			<p class="mut" style="margin:0 0 12px">Cupos: {e.colegios_inscritos}/{e.cupo_colegios} colegios · hasta {e.cupo_estudiantes} estudiantes por colegio</p>
			{#if e.mi_inscripcion}
				<Estado valor={e.mi_inscripcion} />
			{:else}
				<button class="btn" disabled={e.colegios_inscritos >= e.cupo_colegios} onclick={() => abrir(e)}>
					{e.colegios_inscritos >= e.cupo_colegios ? 'Sin cupos' : 'Matricular colegio'}
				</button>
			{/if}
		</div>
	{:else}
		<p class="mut">No hay eventos publicados por ahora.</p>
	{/each}
</div>

{#if sel}
	<Modal titulo={`Matricular en ${sel.nombre}`} cerrar={() => (sel = null)}>
		<form onsubmit={inscribir}>
			<p class="mut">Elige hasta {sel.cupo_estudiantes} estudiantes. Llevas {marcados.length}.</p>
			{#each estudiantes as s}
				<label class="chk"><input type="checkbox" value={s.id} bind:group={marcados} /> {s.nombre} {s.apellido} <span class="mut">· grado {s.grado}</span></label>
			{:else}
				<p class="mut">Primero registra estudiantes en la sección «Estudiantes».</p>
			{/each}
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<div class="row" style="justify-content:flex-end;margin:16px 0 0">
				<button type="button" class="btn o" onclick={() => (sel = null)}>Cancelar</button>
				<button class="btn" disabled={!marcados.length}>Enviar inscripción</button>
			</div>
		</form>
	</Modal>
{/if}
