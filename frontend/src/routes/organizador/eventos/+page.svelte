<script>
	import { onMount } from 'svelte';
	import { api, fechaLarga } from '$lib/api.js';
	import Estado from '$lib/Estado.svelte';
	import Modal from '$lib/Modal.svelte';
	import { avisar } from '$lib/toast.svelte.js';

	let eventos = $state([]);
	let categorias = $state([]);
	let ciudades = $state([]);
	let form = $state(null); // null = cerrado
	let error = $state('');

	async function cargar() {
		try {
			eventos = await api('/organizador/eventos');
		} catch (e) {
			avisar(e.message, true);
		}
	}
	onMount(async () => {
		cargar();
		[categorias, ciudades] = await Promise.all([api('/catalogos/categorias'), api('/catalogos/ciudades')]).catch(() => [[], []]);
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
			await api(id ? `/organizador/eventos/${id}` : '/organizador/eventos', { method: id ? 'PUT' : 'POST', body: cuerpo });
			form = null;
			avisar('Evento guardado como borrador');
			cargar();
		} catch (e) {
			error = e.message;
		}
	}
	async function enviar(id) {
		try {
			await api(`/organizador/eventos/${id}/enviar`, { method: 'POST' });
			avisar('Enviado al administrador para su aprobación');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>Mis eventos | Eventos Escolares</title></svelte:head>

<h2>Mis eventos</h2>
<p class="sub">Crea tus eventos y envíalos al administrador para que los publique.</p>
<div class="row"><button class="btn" onclick={() => abrir(null)}>+ Nuevo evento</button></div>
<div class="card tabla">
	<table>
		<thead><tr><th>Evento</th><th>Fecha</th><th>Lugar</th><th>Cupos</th><th>Estado</th><th></th></tr></thead>
		<tbody>
			{#each eventos as e}
				<tr>
					<td><strong>{e.nombre}</strong><br /><span class="mut">{e.categoria}</span></td>
					<td>{fechaLarga(e.fecha_inicio)}</td><td>{e.lugar}</td><td>{e.colegios_inscritos}/{e.cupo_colegios}</td>
					<td><Estado valor={e.estado} /></td>
					<td>
						{#if e.estado === 'borrador' || e.estado === 'rechazado'}
							<button class="btn o s" onclick={() => abrir(e)}>Editar</button>
						{/if}
						{#if e.estado === 'borrador'}
							<button class="btn s" onclick={() => enviar(e.id)}>Enviar a aprobación</button>
						{/if}
					</td>
				</tr>
			{:else}
				<tr><td colspan="6" class="mut">Todavía no has creado eventos.</td></tr>
			{/each}
		</tbody>
	</table>
</div>

{#if form}
	<Modal titulo={form.id ? 'Editar evento' : 'Nuevo evento'} cerrar={() => (form = null)}>
		<form onsubmit={guardar}>
			<label for="n">Nombre</label>
			<input id="n" required minlength="3" maxlength="150" bind:value={form.nombre} />
			<label for="d">Descripción (opcional)</label>
			<textarea id="d" rows="3" maxlength="500" bind:value={form.descripcion}></textarea>
			<label for="l">Lugar</label>
			<input id="l" required minlength="3" maxlength="150" bind:value={form.lugar} />
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
				<div style="flex:1"><label for="fi">Inicio</label><input id="fi" type="datetime-local" required bind:value={form.fecha_inicio} /></div>
				<div style="flex:1"><label for="ff">Fin (opcional)</label><input id="ff" type="datetime-local" bind:value={form.fecha_fin} /></div>
			</div>
			<div class="row" style="margin:0">
				<div style="flex:1"><label for="cc">Cupo de colegios</label><input id="cc" type="number" min="1" max="1000" required bind:value={form.cupo_colegios} /></div>
				<div style="flex:1"><label for="ce">Estudiantes por colegio</label><input id="ce" type="number" min="1" max="500" required bind:value={form.cupo_estudiantes} /></div>
			</div>
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<div class="row" style="justify-content:flex-end;margin:16px 0 0">
				<button type="button" class="btn o" onclick={() => (form = null)}>Cancelar</button>
				<button class="btn">Guardar borrador</button>
			</div>
		</form>
	</Modal>
{/if}
