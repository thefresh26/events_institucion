<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api.js';
	import Modal from '$lib/Modal.svelte';
	import { avisar } from '$lib/toast.svelte.js';

	let lista = $state([]);
	let ciudades = $state([]);
	let form = $state(null);
	let creado = $state(null); // { colegio, contrasena_temporal }
	let error = $state('');

	async function cargar() {
		try {
			lista = await api('/organizador/colegios');
		} catch (e) {
			avisar(e.message, true);
		}
	}
	onMount(async () => {
		cargar();
		ciudades = await api('/catalogos/ciudades').catch(() => []);
	});

	const vacio = () => ({ colegio_nombre: '', nit: '', id_ciudad: '', direccion: '', telefono: '', nombre: '', apellido: '', correo: '' });
	async function guardar(ev) {
		ev.preventDefault();
		error = '';
		const cuerpo = Object.fromEntries(Object.entries({ ...form, id_ciudad: +form.id_ciudad }).filter(([, v]) => v !== ''));
		try {
			creado = await api('/organizador/colegios', { method: 'POST', body: cuerpo });
			form = null;
			cargar();
		} catch (e) {
			error = e.message;
		}
	}
	async function activar(c, activo) {
		try {
			await api(`/organizador/colegios/${c.id}/activo`, { method: 'PATCH', body: { activo } });
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
	async function eliminar(c) {
		if (!confirm(`¿Eliminar "${c.nombre}" y todos sus estudiantes? Esta acción no se puede deshacer.`)) return;
		try {
			await api(`/organizador/colegios/${c.id}`, { method: 'DELETE' });
			avisar('Colegio eliminado');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>Mis colegios | Conexión Escolar</title></svelte:head>

<h2>Mis colegios</h2>
<p class="sub">Registra a los colegios que participarán en tus eventos. Ellos registran a sus propios estudiantes.</p>
<div class="row"><button class="btn" onclick={() => { error = ''; form = vacio(); }}>+ Registrar colegio</button></div>
<div class="card tabla">
	<table>
		<thead><tr><th>Colegio</th><th>NIT</th><th>Ciudad</th><th>Contacto</th><th>Estado</th><th></th></tr></thead>
		<tbody>
			{#each lista as c}
				<tr>
					<td><strong>{c.nombre}</strong></td><td>{c.nit}</td><td>{c.ciudad}</td><td>{c.contacto}<br /><span class="mut">{c.correo}</span></td>
					<td><span class="b {c.activo ? 'publicado' : 'borrador'}">{c.activo ? 'Activo' : 'Inactivo'}</span></td>
					<td><button class="btn o s" onclick={() => activar(c, !c.activo)}>{c.activo ? 'Desactivar' : 'Activar'}</button> <button class="btn o s" onclick={() => eliminar(c)}>Eliminar</button></td>
				</tr>
			{:else}
				<tr><td colspan="6" class="mut">Aún no has registrado colegios.</td></tr>
			{/each}
		</tbody>
	</table>
</div>

{#if form}
	<Modal titulo="Registrar colegio" cerrar={() => (form = null)}>
		<form onsubmit={guardar}>
			<label for="cn">Nombre del colegio</label><input id="cn" required minlength="3" maxlength="150" bind:value={form.colegio_nombre} />
			<label for="nit">NIT</label><input id="nit" required inputmode="numeric" pattern="[0-9\-]{'{5,20}'}" title="Solo números y guion" bind:value={form.nit} />
			<label for="ci">Ciudad</label>
			<select id="ci" required bind:value={form.id_ciudad}>
				<option value="" disabled>Selecciona…</option>
				{#each ciudades as c}<option value={c.id}>{c.nombre} ({c.departamento})</option>{/each}
			</select>
			<label for="di">Dirección (opcional)</label><input id="di" maxlength="200" bind:value={form.direccion} />
			<label for="te">Teléfono (opcional)</label><input id="te" type="tel" maxlength="20" bind:value={form.telefono} />
			<label for="no">Nombre del contacto (rector o coordinador)</label><input id="no" required minlength="2" maxlength="100" bind:value={form.nombre} />
			<label for="ap">Apellido del contacto</label><input id="ap" required minlength="2" maxlength="100" bind:value={form.apellido} />
			<label for="co">Correo del contacto (será su usuario)</label><input id="co" type="email" required bind:value={form.correo} />
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<div class="row" style="justify-content:flex-end;margin:16px 0 0">
				<button type="button" class="btn o" onclick={() => (form = null)}>Cancelar</button><button class="btn">Registrar</button>
			</div>
		</form>
	</Modal>
{/if}

{#if creado}
	<Modal titulo="Colegio registrado" cerrar={() => (creado = null)}>
		<p>Entrega estos datos al colegio. <strong>La contraseña no se volverá a mostrar</strong>; el colegio debe cambiarla al entrar.</p>
		<p>Usuario: <strong>{creado.colegio.correo}</strong></p>
		<p class="temp">{creado.contrasena_temporal}</p>
		<div class="row" style="justify-content:flex-end;margin:16px 0 0">
			<button class="btn" onclick={() => (creado = null)}>Ya la anoté</button>
		</div>
	</Modal>
{/if}
