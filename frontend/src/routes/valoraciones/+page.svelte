<script>
	import { onMount } from 'svelte';
	import { sesion } from '$lib/session.svelte.js';
	import { listarMisEventos, listarEventosDisponibles, listarEventos } from '$lib/services/api_evento.js';
	import { valoracionesDeEvento, valorarEvento, eliminarValoracion } from '$lib/services/api_aux.js';
	import { fechaLarga } from '$lib/services/api_base.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import Boton from '$lib/components/Boton.svelte';
	import TablaDatos from '$lib/components/TablaDatos.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import { avisar } from '$lib/components/Mensaje.svelte';

	const rol = $derived(sesion.usuario?.rol);
	let eventos = $state([]);
	let evento = $state(''); // evento elegido en la lista
	let datos = $state({ total: 0, promedio: null, valoraciones: [] });
	let form = $state(null); // valorar el evento elegido (solo colegio)
	let porEliminar = $state(null);
	let error = $state('');

	// Cada rol elige entre los eventos que le corresponden
	async function cargarEventos() {
		try {
			eventos = rol === 'colegio' ? await listarEventosDisponibles() : rol === 'administrador' ? await listarEventos() : await listarMisEventos();
			if (eventos.length) { evento = eventos[0].id; cargar(); }
		} catch (e) {
			avisar(e.message, true);
		}
	}
	onMount(() => {
		const espera = setInterval(() => { if (!sesion.cargando) { clearInterval(espera); cargarEventos(); } }, 50);
		return () => clearInterval(espera);
	});

	async function cargar() {
		if (!evento) return;
		try {
			datos = await valoracionesDeEvento(evento);
		} catch (e) {
			avisar(e.message, true);
		}
	}
	async function valorar(ev) {
		ev.preventDefault();
		error = '';
		try {
			await valorarEvento({ id_evento: +evento, puntuacion: +form.puntuacion, ...(form.comentario ? { comentario: form.comentario } : {}) });
			avisar('Gracias por tu valoración');
			form = null;
			cargar();
		} catch (e) {
			error = e.message; // ej. ya valoraste este evento (409)
		}
	}
	async function eliminar() {
		const v = porEliminar;
		porEliminar = null;
		try {
			await eliminarValoracion(v.id);
			avisar('Valoración eliminada');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
	const estrellas = (n) => '★'.repeat(n) + '☆'.repeat(5 - n);
</script>

<svelte:head><title>Valoraciones | Conexión Escolar</title></svelte:head>

<Header titulo="Valoraciones" subtitulo="Qué opinaron los colegios de cada evento." />
<div class="row">
	<select aria-label="Evento" bind:value={evento} onchange={cargar}>{#each eventos as e}<option value={e.id}>{e.nombre}</option>{/each}</select>
	{#if rol === 'colegio' && evento}<Boton onclick={() => { error = ''; form = { puntuacion: 5, comentario: '' }; }}>Valorar este evento</Boton>{/if}
</div>
<p class="note">{datos.total ? `Promedio ${datos.promedio} de 5 · ${datos.total} valoraciones` : 'Este evento todavía no tiene valoraciones.'}</p>
<Card class="tabla">
	<TablaDatos
		filas={datos.valoraciones}
		vacio="No hay valoraciones para este evento."
		columnas={[{ t: 'Puntuación', k: 'puntuacion' }, { t: 'Comentario', k: 'comentario' }, { t: 'Fecha', k: 'creado' }, ...(rol === 'administrador' || rol === 'colegio' ? [{ t: '' }] : [])]}
	>
		{#snippet fila(v)}
			<tr>
				<td>{estrellas(v.puntuacion)}</td><td>{v.comentario ?? ''}</td><td>{fechaLarga(v.creado)}</td>
				{#if rol === 'administrador' || rol === 'colegio'}<td>{#if rol === 'administrador' || v.id_usuario === sesion.usuario.id}<Boton variante="borrar" pequeno onclick={() => (porEliminar = v)}>Eliminar</Boton>{/if}</td>{/if}
			</tr>
		{/snippet}
	</TablaDatos>
</Card>

{#if form}
	<Modal titulo="Valorar evento" cerrar={() => (form = null)}>
		<form onsubmit={valorar}>
			<label for="p">Puntuación</label>
			<select id="p" bind:value={form.puntuacion}>{#each [5, 4, 3, 2, 1] as n}<option value={n}>{estrellas(n)} ({n})</option>{/each}</select>
			<label for="c">Comentario (opcional)</label>
			<textarea id="c" rows="4" maxlength="500" bind:value={form.comentario}></textarea>
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<div class="row" style="justify-content:flex-end;margin:16px 0 0">
				<Boton variante="borde" onclick={() => (form = null)}>Cancelar</Boton><Boton tipo="submit">Enviar</Boton>
			</div>
		</form>
	</Modal>
{/if}

{#if porEliminar}
	<Modal titulo="Eliminar valoración" cerrar={() => (porEliminar = null)}>
		<p>¿Eliminar esta valoración? Deja de mostrarse, pero el registro se conserva.</p>
		<div class="row" style="justify-content:flex-end;margin:16px 0 0">
			<Boton variante="borde" onclick={() => (porEliminar = null)}>Cancelar</Boton><Boton variante="borrar" onclick={eliminar}>Eliminar</Boton>
		</div>
	</Modal>
{/if}
