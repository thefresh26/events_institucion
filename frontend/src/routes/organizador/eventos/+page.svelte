<script>
	import { onMount } from 'svelte';
	import { fechaLarga } from '$lib/services/api_base.js';
	import { listarMisEventos, crearEvento, actualizarEvento, eliminarEvento, enviarEvento } from '$lib/services/api_evento.js';
	import { listarCategorias, listarCiudades } from '$lib/services/api_catalogo.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import Boton from '$lib/components/Boton.svelte';
	import CampoFormulario from '$lib/components/CampoFormulario.svelte';
	import Insignia from '$lib/components/Insignia.svelte';
	import SinDatos from '$lib/components/SinDatos.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import { avisar } from '$lib/components/Mensaje.svelte';

	let eventos = $state([]);
	let categorias = $state([]);
	let ciudades = $state([]);
	let form = $state(null); // null = cerrado
	let error = $state('');
	let porEliminar = $state(null); // evento que se confirma en el Modal
	const ELIMINABLES = ['borrador', 'rechazado', 'cerrado']; // igual que el backend (rutas_eventos.py)

	async function cargar() {
		try {
			eventos = await listarMisEventos();
		} catch (e) {
			avisar(e.message, true);
		}
	}
	onMount(async () => {
		cargar();
		[categorias, ciudades] = await Promise.all([listarCategorias(), listarCiudades()]).catch(() => [[], []]);
	});

	const aLocal = (iso) => (iso ? new Date(new Date(iso).getTime() - new Date(iso).getTimezoneOffset() * 60000).toISOString().slice(0, 16) : '');
	function abrir(e) {
		error = '';
		form = e
			? { id: e.id, nombre: e.nombre, descripcion: e.descripcion ?? '', lugar: e.lugar, fecha_inicio: aLocal(e.fecha_inicio), fecha_fin: aLocal(e.fecha_fin),
				id_categoria: categorias.find((c) => c.nombre === e.categoria)?.id ?? '', id_ciudad: e.id_ciudad, cupo_colegios: e.cupo_colegios, cupo_estudiantes: e.cupo_estudiantes }
			: { id: 0, nombre: '', descripcion: '', lugar: '', fecha_inicio: '', fecha_fin: '', id_categoria: categorias[0]?.id ?? '', id_ciudad: '', cupo_colegios: 10, cupo_estudiantes: 20 };
	}
	async function guardar(ev) {
		ev.preventDefault();
		error = '';
		const { id, ...c } = form;
		const cuerpo = {
			...c, id_categoria: +c.id_categoria, id_ciudad: +c.id_ciudad, cupo_colegios: +c.cupo_colegios, cupo_estudiantes: +c.cupo_estudiantes,
			fecha_inicio: new Date(c.fecha_inicio).toISOString(), fecha_fin: c.fecha_fin ? new Date(c.fecha_fin).toISOString() : null
		};
		try {
			await (id ? actualizarEvento(id, cuerpo) : crearEvento(cuerpo));
			form = null;
			avisar('Evento guardado como borrador');
			cargar();
		} catch (e) {
			error = e.message;
		}
	}
	async function enviar(id) {
		try {
			await enviarEvento(id);
			avisar('Enviado al administrador para su aprobación');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
	async function eliminar() {
		const e = porEliminar;
		porEliminar = null;
		try {
			await eliminarEvento(e.id);
			avisar('Evento eliminado');
			cargar();
		} catch (err) {
			avisar(err.message, true);
		}
	}
</script>

<svelte:head><title>Mis eventos | Conexión Escolar</title></svelte:head>

<Header titulo="Mis eventos" subtitulo="Crea tus eventos y envíalos al administrador para que los publique." />
<div class="row"><Boton onclick={() => abrir(null)}>+ Nuevo evento</Boton></div>
<Card class="tabla">
	<table>
		<thead><tr><th>Evento</th><th>Fecha</th><th>Lugar</th><th>Cupos</th><th>Estado</th><th></th></tr></thead>
		<tbody>
			{#each eventos as e}
				<tr>
					<td><strong>{e.nombre}</strong><br /><span class="mut">{e.categoria}</span></td>
					<td>{fechaLarga(e.fecha_inicio)}</td><td>{e.lugar}</td><td>{e.colegios_inscritos}/{e.cupo_colegios}</td>
					<td><Insignia valor={e.estado} /></td>
					<td>
						{#if ELIMINABLES.includes(e.estado)}
							<div class="row" style="margin:0;flex-wrap:nowrap;white-space:nowrap">
								{#if e.estado !== 'cerrado'}
									<Boton variante="borde" pequeno onclick={() => abrir(e)}>Editar</Boton>
								{/if}
								{#if e.estado === 'borrador'}
									<Boton pequeno onclick={() => enviar(e.id)}>Enviar a aprobación</Boton>
								{/if}
								<Boton variante="borrar" pequeno onclick={() => (porEliminar = e)}>Eliminar</Boton>
							</div>
						{/if}
					</td>
				</tr>
			{:else}
				<SinDatos texto="Todavía no has creado eventos." columnas={6} />
			{/each}
		</tbody>
	</table>
</Card>

{#if form}
	<Modal titulo={form.id ? 'Editar evento' : 'Nuevo evento'} cerrar={() => (form = null)}>
		<form onsubmit={guardar}>
			<CampoFormulario id="n" etiqueta="Nombre" required minlength="3" maxlength="150" bind:value={form.nombre} />
			<label for="d">Descripción (opcional)</label>
			<textarea id="d" rows="3" maxlength="500" bind:value={form.descripcion}></textarea>
			<CampoFormulario id="l" etiqueta="Lugar" required minlength="3" maxlength="150" bind:value={form.lugar} />
			<label for="c">Ciudad</label>
			<select id="c" required bind:value={form.id_ciudad}>
				<option value="" disabled>Selecciona…</option>
				{#each ciudades as c}<option value={c.id}>{c.nombre} ({c.departamento})</option>{/each}
			</select>
			<label for="k">Categoría</label>
			<select id="k" required bind:value={form.id_categoria}>
				{#each categorias as c}<option value={c.id}>{c.nombre}</option>{/each}
			</select>
			<div class="row" style="margin:0">
				<div style="flex:1"><CampoFormulario id="fi" etiqueta="Inicio" tipo="datetime-local" required bind:value={form.fecha_inicio} /></div>
				<div style="flex:1"><CampoFormulario id="ff" etiqueta="Fin (opcional)" tipo="datetime-local" bind:value={form.fecha_fin} /></div>
			</div>
			<div class="row" style="margin:0">
				<div style="flex:1"><CampoFormulario id="cc" etiqueta="Cupo de colegios" tipo="number" min="1" max="1000" required bind:value={form.cupo_colegios} /></div>
				<div style="flex:1"><CampoFormulario id="ce" etiqueta="Estudiantes por colegio" tipo="number" min="1" max="500" required bind:value={form.cupo_estudiantes} /></div>
			</div>
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<div class="row" style="justify-content:flex-end;margin:16px 0 0">
				<Boton variante="borde" onclick={() => (form = null)}>Cancelar</Boton>
				<Boton tipo="submit">Guardar borrador</Boton>
			</div>
		</form>
	</Modal>
{/if}

{#if porEliminar}
	<Modal titulo="Eliminar evento" cerrar={() => (porEliminar = null)}>
		<p>¿Eliminar <strong>{porEliminar.nombre}</strong>? Dejará de aparecer en tus eventos.</p>
		<div class="row" style="justify-content:flex-end;margin:16px 0 0">
			<Boton variante="borde" onclick={() => (porEliminar = null)}>Cancelar</Boton><Boton variante="borrar" onclick={eliminar}>Eliminar</Boton>
		</div>
	</Modal>
{/if}
