<script>
	import { onMount } from 'svelte';
	import { api, fechaLarga } from '$lib/api.js';
	import { avisar } from '$lib/toast.svelte.js';
	import { sesion } from '$lib/session.svelte.js';
	import Modal from '$lib/Modal.svelte';

	const ROLES = { administrador: 'Administrador', organizador: 'Organizador', colegio: 'Colegio' };
	let lista = $state([]);
	let cargando = $state(true);
	let filtro = $state({ q: '', rol: '', estado: '' });
	let nuevo = $state(null); // formulario de creacion
	let edita = $state(null); // usuario en edicion
	let clave = $state(null); // { correo, temporal } mostrado una sola vez
	let error = $state('');
	let t;

	async function cargar() {
		const p = new URLSearchParams(Object.entries(filtro).filter(([, v]) => v));
		try {
			lista = await api('/admin/usuarios' + (p.size ? `?${p}` : ''));
		} catch (e) {
			avisar(e.message, true);
		}
		cargando = false;
	}
	onMount(cargar);
	function buscar() {
		clearTimeout(t);
		t = setTimeout(cargar, 300);
	}

	const formNuevo = () => ({ rol: 'administrador', correo: '', nombre: '', apellido: '', organizacion_nombre: '', nit: '', telefono: '' });

	async function crear(e) {
		e.preventDefault();
		error = '';
		const cuerpo = Object.fromEntries(Object.entries(nuevo).filter(([, v]) => v !== ''));
		try {
			const r = await api('/admin/usuarios', { method: 'POST', body: cuerpo });
			clave = { correo: r.usuario.correo, temporal: r.contrasena_temporal };
			nuevo = null;
			cargar();
		} catch (err) {
			error = err.message;
		}
	}

	async function guardar(e) {
		e.preventDefault();
		error = '';
		try {
			await api(`/admin/usuarios/${edita.id}`, { method: 'PATCH', body: { nombre: edita.nombre, apellido: edita.apellido, rol: edita.rol } });
			avisar('Usuario actualizado');
			edita = null;
			cargar();
		} catch (err) {
			error = err.message;
		}
	}

	async function activar(u, activo) {
		try {
			await api(`/admin/usuarios/${u.id}`, { method: 'PATCH', body: { activo } });
			avisar(activo ? 'Usuario activado' : 'Usuario desactivado');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}

	async function restablecer(u) {
		if (!confirm(`¿Restablecer la contraseña de ${u.correo}? La anterior dejará de funcionar.`)) return;
		try {
			const r = await api(`/admin/usuarios/${u.id}/restablecer`, { method: 'POST' });
			clave = { correo: u.correo, temporal: r.contrasena_temporal };
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>Usuarios | Conexión Escolar</title></svelte:head>

<h2>Usuarios</h2>
<p class="sub">Crea cuentas, cambia roles, activa o desactiva el acceso y restablece contraseñas.</p>

<div class="row">
	<input type="search" placeholder="Buscar por nombre o correo" aria-label="Buscar usuarios" bind:value={filtro.q} oninput={buscar} style="min-width:240px" />
	<select aria-label="Filtrar por rol" bind:value={filtro.rol} onchange={cargar}>
		<option value="">Todos los roles</option>
		{#each Object.entries(ROLES) as [k, v]}<option value={k}>{v}</option>{/each}
	</select>
	<select aria-label="Filtrar por estado" bind:value={filtro.estado} onchange={cargar}>
		<option value="">Todos los estados</option>
		<option value="activo">Activos</option>
		<option value="inactivo">Inactivos / pendientes</option>
	</select>
	<button class="btn" style="margin-left:auto" onclick={() => { error = ''; nuevo = formNuevo(); }}>+ Nuevo usuario</button>
</div>

<div class="card tabla">
	<table>
		<thead><tr><th>Usuario</th><th>Rol</th><th>Perfil</th><th>Creado</th><th>Estado</th><th></th></tr></thead>
		<tbody>
			{#each lista as u (u.id)}
				<tr>
					<td><strong>{u.nombre} {u.apellido}</strong><br /><span class="mut">{u.correo}</span></td>
					<td><span class="b {u.rol === 'administrador' ? 'cerrado' : u.rol === 'organizador' ? 'pendiente' : 'borrador'}">{ROLES[u.rol] ?? u.rol}</span></td>
					<td>{u.perfil ?? '—'}</td>
					<td class="mut">{fechaLarga(u.creado_en)}</td>
					<td><span class="b {u.activo ? 'publicado' : 'rechazado'}">{u.activo ? 'Activo' : 'Inactivo'}</span></td>
					<td>
						<div class="row" style="margin:0;flex-wrap:nowrap">
							<button class="btn o s" onclick={() => { error = ''; edita = { ...u }; }}>Editar</button>
							{#if u.id !== sesion.usuario.id}
								<button class="btn o s" onclick={() => restablecer(u)}>Restablecer clave</button>
								{#if u.activo}
									<button class="btn o s" onclick={() => activar(u, false)}>Desactivar</button>
								{:else}
									<button class="btn s" onclick={() => activar(u, true)}>Activar</button>
								{/if}
							{:else}
								<span class="mut">(tú)</span>
							{/if}
						</div>
					</td>
				</tr>
			{:else}
				<tr><td colspan="6" class="mut">{cargando ? 'Cargando…' : 'No hay usuarios con esos filtros.'}</td></tr>
			{/each}
		</tbody>
	</table>
</div>

{#if nuevo}
	<Modal titulo="Nuevo usuario" cerrar={() => (nuevo = null)}>
		<form onsubmit={crear}>
			<label for="nr">Rol</label>
			<select id="nr" bind:value={nuevo.rol}>
				<option value="administrador">Administrador</option>
				<option value="organizador">Organizador (para probar o gestionar eventos)</option>
			</select>
			{#if nuevo.rol === 'organizador'}
				<label for="no">Nombre de la organización</label>
				<input id="no" required minlength="3" maxlength="150" bind:value={nuevo.organizacion_nombre} />
				<label for="nn">NIT</label>
				<input id="nn" required inputmode="numeric" pattern={'[0-9\\-]{5,20}'} title="Solo números y guion" bind:value={nuevo.nit} />
				<label for="nt">Teléfono (opcional)</label>
				<input id="nt" type="tel" maxlength="20" bind:value={nuevo.telefono} />
			{/if}
			<label for="nm">Nombre</label>
			<input id="nm" required minlength="2" maxlength="100" bind:value={nuevo.nombre} />
			<label for="na">Apellido</label>
			<input id="na" required minlength="2" maxlength="100" bind:value={nuevo.apellido} />
			<label for="nc">Correo (será su usuario)</label>
			<input id="nc" type="email" required bind:value={nuevo.correo} />
			<p class="note">Se genera una contraseña temporal que verás una sola vez. La cuenta queda activa de inmediato.</p>
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<div class="row" style="justify-content:flex-end;margin:16px 0 0">
				<button type="button" class="btn o" onclick={() => (nuevo = null)}>Cancelar</button>
				<button class="btn">Crear usuario</button>
			</div>
		</form>
	</Modal>
{/if}

{#if edita}
	<Modal titulo="Editar usuario" cerrar={() => (edita = null)}>
		<form onsubmit={guardar}>
			<p class="mut" style="margin:0">{edita.correo}</p>
			<label for="en">Nombre</label>
			<input id="en" required minlength="2" maxlength="100" bind:value={edita.nombre} />
			<label for="ea">Apellido</label>
			<input id="ea" required minlength="2" maxlength="100" bind:value={edita.apellido} />
			<label for="er">Rol</label>
			<select id="er" bind:value={edita.rol} disabled={edita.id === sesion.usuario.id}>
				{#each Object.entries(ROLES) as [k, v]}<option value={k}>{v}</option>{/each}
			</select>
			<p class="note">Un usuario solo puede pasar a organizador o colegio si ya tiene ese perfil; a administrador siempre puede pasar.</p>
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<div class="row" style="justify-content:flex-end;margin:16px 0 0">
				<button type="button" class="btn o" onclick={() => (edita = null)}>Cancelar</button>
				<button class="btn">Guardar</button>
			</div>
		</form>
	</Modal>
{/if}

{#if clave}
	<Modal titulo="Contraseña temporal" cerrar={() => (clave = null)}>
		<p>Entrega estos datos a la persona. <strong>La contraseña no se volverá a mostrar</strong>; debe cambiarla al entrar (Mi cuenta).</p>
		<p>Usuario: <strong>{clave.correo}</strong></p>
		<p class="temp">{clave.temporal}</p>
		<div class="row" style="justify-content:flex-end;margin:16px 0 0"><button class="btn" onclick={() => (clave = null)}>Ya la anoté</button></div>
	</Modal>
{/if}
