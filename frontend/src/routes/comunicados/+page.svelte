<script>
	import { onMount } from 'svelte';
	import { sesion } from '$lib/session.svelte.js';
	import { listarComunicados, crearComunicado, actualizarComunicado, eliminarComunicado } from '$lib/services/api_aux.js';
	import { fechaLarga } from '$lib/services/api_base.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import Boton from '$lib/components/Boton.svelte';
	import CampoFormulario from '$lib/components/CampoFormulario.svelte';
	import TablaDatos from '$lib/components/TablaDatos.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import { avisar } from '$lib/components/Mensaje.svelte';

	const esAdmin = $derived(sesion.usuario?.rol === 'administrador');
	const DESTINO = { todos: 'Todos', organizador: 'Organizadores', colegio: 'Colegios' };
	let lista = $state([]);
	let form = $state(null); // id = 0: publicar; id > 0: editar
	let porEliminar = $state(null);
	let error = $state('');

	async function cargar() {
		try {
			lista = await listarComunicados();
		} catch (e) {
			avisar(e.message, true);
		}
	}
	onMount(cargar);

	async function guardar(ev) {
		ev.preventDefault();
		error = '';
		const datos = { titulo: form.titulo, contenido: form.contenido, dirigido_a: form.dirigido_a };
		try {
			if (form.id) await actualizarComunicado(form.id, datos);
			else await crearComunicado(datos);
			avisar(form.id ? 'Comunicado actualizado' : 'Comunicado publicado');
			form = null;
			cargar();
		} catch (e) {
			error = e.message; // ej. ya existe un comunicado con ese titulo (409)
		}
	}
	async function eliminar() {
		const c = porEliminar;
		porEliminar = null;
		try {
			await eliminarComunicado(c.id);
			avisar('Comunicado eliminado');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>Comunicados | Conexión Escolar</title></svelte:head>

<Header titulo="Comunicados" subtitulo={esAdmin ? 'Publica avisos para organizadores y colegios.' : 'Avisos de la plataforma dirigidos a tu rol.'} />
{#if esAdmin}<div class="row"><Boton onclick={() => { error = ''; form = { id: 0, titulo: '', contenido: '', dirigido_a: 'todos' }; }}>+ Publicar comunicado</Boton></div>{/if}
<Card class="tabla">
	<TablaDatos
		filas={lista}
		vacio="No hay comunicados para tu rol."
		columnas={[{ t: 'Título', k: 'titulo' }, { t: 'Contenido', k: 'contenido' }, { t: 'Dirigido a', k: (c) => DESTINO[c.dirigido_a] }, { t: 'Fecha', k: 'creado' }, ...(esAdmin ? [{ t: '' }] : [])]}
	>
		{#snippet fila(c)}
			<tr>
				<td>{c.titulo}</td><td>{c.contenido}</td><td>{DESTINO[c.dirigido_a]}</td><td>{fechaLarga(c.creado)}</td>
				{#if esAdmin}
					<td><div class="row" style="margin:0;flex-wrap:nowrap">
						<Boton variante="borde" pequeno onclick={() => { error = ''; form = { id: c.id, titulo: c.titulo, contenido: c.contenido, dirigido_a: c.dirigido_a }; }}>Editar</Boton>
						<Boton variante="borrar" pequeno onclick={() => (porEliminar = c)}>Eliminar</Boton>
					</div></td>
				{/if}
			</tr>
		{/snippet}
	</TablaDatos>
</Card>

{#if form}
	<Modal titulo={form.id ? 'Editar comunicado' : 'Publicar comunicado'} cerrar={() => (form = null)}>
		<form onsubmit={guardar}>
			<CampoFormulario id="ti" etiqueta="Título" required minlength="3" maxlength="150" bind:value={form.titulo} />
			<label for="co">Contenido</label>
			<textarea id="co" rows="5" required minlength="5" maxlength="2000" bind:value={form.contenido}></textarea>
			<label for="di">Dirigido a</label>
			<select id="di" bind:value={form.dirigido_a}>{#each Object.entries(DESTINO) as [valor, nombre]}<option value={valor}>{nombre}</option>{/each}</select>
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<div class="row" style="justify-content:flex-end;margin:16px 0 0">
				<Boton variante="borde" onclick={() => (form = null)}>Cancelar</Boton><Boton tipo="submit">Guardar</Boton>
			</div>
		</form>
	</Modal>
{/if}

{#if porEliminar}
	<Modal titulo="Eliminar comunicado" cerrar={() => (porEliminar = null)}>
		<p>¿Eliminar el comunicado <strong>{porEliminar.titulo}</strong>? Deja de mostrarse, pero el registro se conserva.</p>
		<div class="row" style="justify-content:flex-end;margin:16px 0 0">
			<Boton variante="borde" onclick={() => (porEliminar = null)}>Cancelar</Boton><Boton variante="borrar" onclick={eliminar}>Eliminar</Boton>
		</div>
	</Modal>
{/if}
