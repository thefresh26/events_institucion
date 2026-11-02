<script>
	import { onMount } from 'svelte';
	import { sesion } from '$lib/session.svelte.js';
	import { listarTipos, listarPqrs, radicarPqrs, responderPqrs, eliminarPqrs } from '$lib/services/api_aux.js';
	import { fechaLarga } from '$lib/services/api_base.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import Boton from '$lib/components/Boton.svelte';
	import CampoFormulario from '$lib/components/CampoFormulario.svelte';
	import TablaDatos from '$lib/components/TablaDatos.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import { avisar } from '$lib/components/Mensaje.svelte';

	const esAdmin = $derived(sesion.usuario?.rol === 'administrador');
	let lista = $state([]);
	let tipos = $state([]);
	let form = $state(null); // radicar una PQRS nueva
	let respondiendo = $state(null); // PQRS que el administrador contesta
	let porEliminar = $state(null);
	let error = $state('');

	async function cargar() {
		try {
			lista = await listarPqrs();
		} catch (e) {
			avisar(e.message, true);
		}
	}
	onMount(async () => {
		cargar();
		tipos = await listarTipos().catch(() => []);
	});

	async function enviar(ev) {
		ev.preventDefault();
		error = '';
		try {
			await radicarPqrs({ id_tipo: +form.id_tipo, asunto: form.asunto, mensaje: form.mensaje });
			avisar('PQRS radicada');
			form = null;
			cargar();
		} catch (e) {
			error = e.message;
		}
	}
	async function responder(ev) {
		ev.preventDefault();
		error = '';
		try {
			await responderPqrs(respondiendo.id, respondiendo.texto);
			avisar('Respuesta enviada');
			respondiendo = null;
			cargar();
		} catch (e) {
			error = e.message;
		}
	}
	async function eliminar() {
		const p = porEliminar;
		porEliminar = null;
		try {
			await eliminarPqrs(p.id);
			avisar('PQRS eliminada');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>PQRS | Conexión Escolar</title></svelte:head>

<Header titulo="PQRS" subtitulo={esAdmin ? 'Peticiones, quejas, reclamos y sugerencias de todos los usuarios.' : 'Escribe tu petición, queja, reclamo o sugerencia y revisa la respuesta.'} />
<div class="row"><Boton onclick={() => { error = ''; form = { id_tipo: tipos[0]?.id ?? '', asunto: '', mensaje: '' }; }}>+ Radicar PQRS</Boton></div>
<Card class="tabla">
	<TablaDatos
		filas={lista}
		vacio="Aún no hay PQRS."
		columnas={[{ t: 'Radicado', k: 'radicado' }, { t: 'Tipo', k: 'tipo' }, { t: 'Asunto', k: 'asunto' }, { t: 'Estado', k: (p) => (p.respuesta ? 'Respondida' : 'Pendiente') }, { t: 'Fecha', k: 'creado' }, { t: '' }]}
	>
		{#snippet fila(p)}
			<tr>
				<td>{p.radicado}</td><td>{p.tipo}</td>
				<td>{p.asunto}<br /><small>{p.mensaje}</small>{#if p.respuesta}<br /><small><strong>Respuesta:</strong> {p.respuesta}</small>{/if}</td>
				<td>{p.respuesta ? 'Respondida' : 'Pendiente'}</td><td>{fechaLarga(p.creado)}</td>
				<td>
					{#if esAdmin}
						<div class="row" style="margin:0;flex-wrap:nowrap">
							<Boton variante="borde" pequeno onclick={() => { error = ''; respondiendo = { id: p.id, asunto: p.asunto, texto: p.respuesta ?? '' }; }}>Responder</Boton>
							<Boton variante="borrar" pequeno onclick={() => (porEliminar = p)}>Eliminar</Boton>
						</div>
					{/if}
				</td>
			</tr>
		{/snippet}
	</TablaDatos>
</Card>

{#if form}
	<Modal titulo="Radicar PQRS" cerrar={() => (form = null)}>
		<form onsubmit={enviar}>
			<label for="t">Tipo</label>
			<select id="t" required bind:value={form.id_tipo}>{#each tipos as t}<option value={t.id}>{t.nombre}</option>{/each}</select>
			<CampoFormulario id="as" etiqueta="Asunto" required minlength="3" maxlength="150" bind:value={form.asunto} />
			<label for="m">Mensaje</label>
			<textarea id="m" rows="5" required minlength="5" maxlength="1000" bind:value={form.mensaje}></textarea>
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<div class="row" style="justify-content:flex-end;margin:16px 0 0">
				<Boton variante="borde" onclick={() => (form = null)}>Cancelar</Boton><Boton tipo="submit">Enviar</Boton>
			</div>
		</form>
	</Modal>
{/if}

{#if respondiendo}
	<Modal titulo="Responder PQRS" cerrar={() => (respondiendo = null)}>
		<form onsubmit={responder}>
			<p><strong>{respondiendo.asunto}</strong></p>
			<label for="r">Respuesta</label>
			<textarea id="r" rows="5" required minlength="3" maxlength="1000" bind:value={respondiendo.texto}></textarea>
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<div class="row" style="justify-content:flex-end;margin:16px 0 0">
				<Boton variante="borde" onclick={() => (respondiendo = null)}>Cancelar</Boton><Boton tipo="submit">Responder</Boton>
			</div>
		</form>
	</Modal>
{/if}

{#if porEliminar}
	<Modal titulo="Eliminar PQRS" cerrar={() => (porEliminar = null)}>
		<p>¿Eliminar la PQRS <strong>{porEliminar.asunto}</strong>? Deja de mostrarse, pero el registro se conserva.</p>
		<div class="row" style="justify-content:flex-end;margin:16px 0 0">
			<Boton variante="borde" onclick={() => (porEliminar = null)}>Cancelar</Boton><Boton variante="borrar" onclick={eliminar}>Eliminar</Boton>
		</div>
	</Modal>
{/if}
