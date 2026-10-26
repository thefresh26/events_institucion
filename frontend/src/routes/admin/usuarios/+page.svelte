<script>
	import { onMount } from 'svelte';
	import { fechaLarga } from '$lib/services/api_base.js';
	import { listarUsuarios, crearUsuario, actualizarUsuario, eliminarUsuario, restablecerContrasena } from '$lib/services/api_usuario.js';
	import { sesion } from '$lib/session.svelte.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import Boton from '$lib/components/Boton.svelte';
	import CampoFormulario from '$lib/components/CampoFormulario.svelte';
	import Insignia from '$lib/components/Insignia.svelte';
	import SinDatos from '$lib/components/SinDatos.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import { avisar } from '$lib/components/Mensaje.svelte';

	const ROLES = { administrador: 'Administrador', organizador: 'Organizador', colegio: 'Colegio' };
	const COLOR_ROL = { administrador: 'cerrado', organizador: 'pendiente', colegio: 'borrador' }; // colores de Insignia
	let lista = $state([]);
	let cargando = $state(true);
	let filtro = $state({ q: '', rol: '', estado: '' });
	let nuevo = $state(null); // formulario de creacion
	let edita = $state(null); // usuario en edicion
	let clave = $state(null); // { correo, temporal } mostrado una sola vez
	let confirmar = $state(null); // { usuario, accion: 'eliminar' | 'restablecer' } confirmado en el Modal
	let error = $state('');
	let t;

	async function cargar() {
		try {
			lista = await listarUsuarios(filtro);
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
			const r = await crearUsuario(cuerpo);
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
			await actualizarUsuario(edita.id, { nombre: edita.nombre, apellido: edita.apellido, rol: edita.rol });
			avisar('Usuario actualizado');
			edita = null;
			cargar();
		} catch (err) {
			error = err.message;
		}
	}

	async function activar(u, activo) {
		try {
			await actualizarUsuario(u.id, { activo });
			avisar(activo ? 'Usuario activado' : 'Usuario desactivado');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}

	async function confirmado() {
		const { usuario: u, accion } = confirmar;
		confirmar = null;
		try {
			if (accion === 'eliminar') {
				await eliminarUsuario(u.id);
				avisar('Usuario eliminado');
				cargar();
			} else {
				const r = await restablecerContrasena(u.id);
				clave = { correo: u.correo, temporal: r.contrasena_temporal };
			}
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>Usuarios | Conexión Escolar</title></svelte:head>

<Header titulo="Usuarios" subtitulo="Crea cuentas, cambia roles, activa o desactiva el acceso y restablece contraseñas." />

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
	<span style="margin-left:auto"><Boton onclick={() => { error = ''; nuevo = formNuevo(); }}>+ Nuevo usuario</Boton></span>
</div>

<Card class="tabla">
	<table>
		<thead><tr><th>Usuario</th><th>Rol</th><th>Perfil</th><th>Creado</th><th>Estado</th><th></th></tr></thead>
		<tbody>
			{#each lista as u (u.id)}
				<tr>
					<td><strong>{u.nombre} {u.apellido}</strong><br /><span class="mut">{u.correo}</span></td>
					<td><Insignia valor={COLOR_ROL[u.rol] ?? 'borrador'} texto={ROLES[u.rol] ?? u.rol} /></td>
					<td>{u.perfil ?? '—'}</td>
					<td class="mut">{fechaLarga(u.creado_en)}</td>
					<td><Insignia valor={u.activo ? 'publicado' : 'rechazado'} texto={u.activo ? 'Activo' : 'Inactivo'} /></td>
					<td>
						<div class="row" style="margin:0;flex-wrap:nowrap">
							<Boton variante="borde" pequeno onclick={() => { error = ''; edita = { ...u }; }}>Editar</Boton>
							{#if u.id !== sesion.usuario.id}
								<Boton variante="borde" pequeno onclick={() => (confirmar = { usuario: u, accion: 'restablecer' })}>Restablecer clave</Boton>
								{#if u.activo}
									<Boton variante="borde" pequeno onclick={() => activar(u, false)}>Desactivar</Boton>
								{:else}
									<Boton pequeno onclick={() => activar(u, true)}>Activar</Boton>
								{/if}
								<Boton variante="borrar" pequeno onclick={() => (confirmar = { usuario: u, accion: 'eliminar' })}>Eliminar</Boton>
							{:else}
								<span class="mut">(tú)</span>
							{/if}
						</div>
					</td>
				</tr>
			{:else}
				<SinDatos texto={cargando ? 'Cargando…' : 'No hay usuarios con esos filtros.'} columnas={6} />
			{/each}
		</tbody>
	</table>
</Card>

{#if nuevo}
	<Modal titulo="Nuevo usuario" cerrar={() => (nuevo = null)}>
		<form onsubmit={crear}>
			<label for="nr">Rol</label>
			<select id="nr" bind:value={nuevo.rol}>
				<option value="administrador">Administrador</option>
				<option value="organizador">Organizador (para probar o gestionar eventos)</option>
			</select>
			{#if nuevo.rol === 'organizador'}
				<CampoFormulario id="no" etiqueta="Nombre de la organización" required minlength="3" maxlength="150" bind:value={nuevo.organizacion_nombre} />
				<CampoFormulario id="nn" etiqueta="NIT" required inputmode="numeric" pattern={'[0-9\\-]{5,20}'} title="Solo números y guion" bind:value={nuevo.nit} />
				<CampoFormulario id="nt" etiqueta="Teléfono (opcional)" tipo="tel" maxlength="20" bind:value={nuevo.telefono} />
			{/if}
			<CampoFormulario id="nm" etiqueta="Nombre" required minlength="2" maxlength="100" bind:value={nuevo.nombre} />
			<CampoFormulario id="na" etiqueta="Apellido" required minlength="2" maxlength="100" bind:value={nuevo.apellido} />
			<CampoFormulario id="nc" etiqueta="Correo (será su usuario)" tipo="email" required bind:value={nuevo.correo} />
			<p class="note">Se genera una contraseña temporal que verás una sola vez. La cuenta queda activa de inmediato.</p>
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<div class="row" style="justify-content:flex-end;margin:16px 0 0">
				<Boton variante="borde" onclick={() => (nuevo = null)}>Cancelar</Boton>
				<Boton tipo="submit">Crear usuario</Boton>
			</div>
		</form>
	</Modal>
{/if}

{#if edita}
	<Modal titulo="Editar usuario" cerrar={() => (edita = null)}>
		<form onsubmit={guardar}>
			<p class="mut" style="margin:0">{edita.correo}</p>
			<CampoFormulario id="en" etiqueta="Nombre" required minlength="2" maxlength="100" bind:value={edita.nombre} />
			<CampoFormulario id="ea" etiqueta="Apellido" required minlength="2" maxlength="100" bind:value={edita.apellido} />
			<label for="er">Rol</label>
			<select id="er" bind:value={edita.rol} disabled={edita.id === sesion.usuario.id}>
				{#each Object.entries(ROLES) as [k, v]}<option value={k}>{v}</option>{/each}
			</select>
			<p class="note">Un usuario solo puede pasar a organizador o colegio si ya tiene ese perfil; a administrador siempre puede pasar.</p>
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<div class="row" style="justify-content:flex-end;margin:16px 0 0">
				<Boton variante="borde" onclick={() => (edita = null)}>Cancelar</Boton>
				<Boton tipo="submit">Guardar</Boton>
			</div>
		</form>
	</Modal>
{/if}

{#if confirmar}
	<Modal titulo={confirmar.accion === 'eliminar' ? 'Eliminar usuario' : 'Restablecer contraseña'} cerrar={() => (confirmar = null)}>
		{#if confirmar.accion === 'eliminar'}
			<p>¿Eliminar a <strong>{confirmar.usuario.correo}</strong>? Esta acción no se puede deshacer.</p>
		{:else}
			<p>¿Restablecer la contraseña de <strong>{confirmar.usuario.correo}</strong>? La anterior dejará de funcionar.</p>
		{/if}
		<div class="row" style="justify-content:flex-end;margin:16px 0 0">
			<Boton variante="borde" onclick={() => (confirmar = null)}>Cancelar</Boton>
			<Boton variante={confirmar.accion === 'eliminar' ? 'borrar' : 'primario'} onclick={confirmado}>
				{confirmar.accion === 'eliminar' ? 'Eliminar' : 'Restablecer'}
			</Boton>
		</div>
	</Modal>
{/if}

{#if clave}
	<Modal titulo="Contraseña temporal" cerrar={() => (clave = null)}>
		<p>Entrega estos datos a la persona. <strong>La contraseña no se volverá a mostrar</strong>; debe cambiarla al entrar (Mi cuenta).</p>
		<p>Usuario: <strong>{clave.correo}</strong></p>
		<p class="temp">{clave.temporal}</p>
		<div class="row" style="justify-content:flex-end;margin:16px 0 0"><Boton onclick={() => (clave = null)}>Ya la anoté</Boton></div>
	</Modal>
{/if}
