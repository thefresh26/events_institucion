<script>
	import { onMount } from 'svelte';
	import { listarMisColegios, crearColegio, activarColegio, eliminarColegio } from '$lib/services/api_colegio.js';
	import { listarCiudades } from '$lib/services/api_catalogo.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import Boton from '$lib/components/Boton.svelte';
	import CampoFormulario from '$lib/components/CampoFormulario.svelte';
	import Insignia from '$lib/components/Insignia.svelte';
	import TablaDatos from '$lib/components/TablaDatos.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import { avisar } from '$lib/components/Mensaje.svelte';

	let lista = $state([]);
	let ciudades = $state([]);
	let form = $state(null);
	let creado = $state(null); // { colegio, contrasena_temporal }
	let error = $state('');
	let porEliminar = $state(null); // colegio que se confirma en el Modal

	async function cargar() {
		try {
			lista = await listarMisColegios();
		} catch (e) {
			avisar(e.message, true);
		}
	}
	onMount(async () => {
		cargar();
		ciudades = await listarCiudades().catch(() => []);
	});

	const vacio = () => ({ colegio_nombre: '', nit: '', id_ciudad: '', direccion: '', telefono: '', nombre: '', apellido: '', correo: '' });
	async function guardar(ev) {
		ev.preventDefault();
		error = '';
		const cuerpo = Object.fromEntries(Object.entries({ ...form, id_ciudad: +form.id_ciudad }).filter(([, v]) => v !== ''));
		try {
			creado = await crearColegio(cuerpo);
			form = null;
			cargar();
		} catch (e) {
			error = e.message;
		}
	}
	async function activar(c, activo) {
		try {
			await activarColegio(c.id, activo);
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
	async function eliminar() {
		const c = porEliminar;
		porEliminar = null;
		try {
			await eliminarColegio(c.id);
			avisar('Colegio eliminado');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>Mis colegios | Conexión Escolar</title></svelte:head>

<Header titulo="Mis colegios" subtitulo="Registra a los colegios que participarán en tus eventos. Ellos registran a sus propios estudiantes." />
<div class="row"><Boton onclick={() => { error = ''; form = vacio(); }}>+ Registrar colegio</Boton></div>
<Card class="tabla">
	<TablaDatos
		filas={lista}
		vacio="Aún no has registrado colegios."
		columnas={[{ t: 'Colegio', k: 'nombre' }, { t: 'NIT', k: 'nit' }, { t: 'Ciudad', k: 'ciudad' }, { t: 'Contacto', k: 'contacto' }, { t: 'Estado', k: 'activo' }, { t: '' }]}
	>
		{#snippet fila(c)}
			<tr>
				<td><strong>{c.nombre}</strong></td><td>{c.nit}</td><td>{c.ciudad}</td><td>{c.contacto}<br /><span class="mut">{c.correo}</span></td>
				<td><Insignia valor={c.activo ? 'publicado' : 'borrador'} texto={c.activo ? 'Activo' : 'Inactivo'} /></td>
				<td>
					<div class="row" style="margin:0;flex-wrap:wrap">
						<Boton variante="borde" pequeno onclick={() => activar(c, !c.activo)}>{c.activo ? 'Desactivar' : 'Activar'}</Boton>
						<Boton variante="borrar" pequeno onclick={() => (porEliminar = c)}>Eliminar</Boton>
					</div>
				</td>
			</tr>
		{/snippet}
	</TablaDatos>
</Card>

{#if form}
	<Modal titulo="Registrar colegio" cerrar={() => (form = null)}>
		<form onsubmit={guardar}>
			<CampoFormulario id="cn" etiqueta="Nombre del colegio" required minlength="3" maxlength="150" bind:value={form.colegio_nombre} />
			<CampoFormulario id="nit" etiqueta="NIT" required inputmode="numeric" pattern={'[0-9\\-]{5,20}'} title="Solo números y guion" bind:value={form.nit} />
			<label for="ci">Ciudad</label>
			<select id="ci" required bind:value={form.id_ciudad}>
				<option value="" disabled>Selecciona…</option>
				{#each ciudades as c}<option value={c.id}>{c.nombre} ({c.departamento})</option>{/each}
			</select>
			<CampoFormulario id="di" etiqueta="Dirección (opcional)" maxlength="200" bind:value={form.direccion} />
			<CampoFormulario id="te" etiqueta="Teléfono (opcional)" tipo="tel" maxlength="20" bind:value={form.telefono} />
			<CampoFormulario id="no" etiqueta="Nombre del contacto (rector o coordinador)" required minlength="2" maxlength="100" bind:value={form.nombre} />
			<CampoFormulario id="ap" etiqueta="Apellido del contacto" required minlength="2" maxlength="100" bind:value={form.apellido} />
			<CampoFormulario id="co" etiqueta="Correo del contacto (será su usuario)" tipo="email" required bind:value={form.correo} />
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<div class="row" style="justify-content:flex-end;margin:16px 0 0">
				<Boton variante="borde" onclick={() => (form = null)}>Cancelar</Boton><Boton tipo="submit">Registrar</Boton>
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
			<Boton onclick={() => (creado = null)}>Ya la anoté</Boton>
		</div>
	</Modal>
{/if}

{#if porEliminar}
	<Modal titulo="Eliminar colegio" cerrar={() => (porEliminar = null)}>
		<p>¿Eliminar <strong>{porEliminar.nombre}</strong> y todos sus estudiantes? Esta acción no se puede deshacer.</p>
		<div class="row" style="justify-content:flex-end;margin:16px 0 0">
			<Boton variante="borde" onclick={() => (porEliminar = null)}>Cancelar</Boton><Boton variante="borrar" onclick={eliminar}>Eliminar</Boton>
		</div>
	</Modal>
{/if}
