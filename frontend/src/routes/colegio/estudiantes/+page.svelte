<script>
	import { onMount } from 'svelte';
	import { listarEstudiantes, crearEstudiante, obtenerEstudiante, actualizarEstudiante, eliminarEstudiante } from '$lib/services/api_estudiante.js';
	import { listarGrados } from '$lib/services/api_catalogo.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import Boton from '$lib/components/Boton.svelte';
	import CampoFormulario from '$lib/components/CampoFormulario.svelte';
	import SinDatos from '$lib/components/SinDatos.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import { avisar } from '$lib/components/Mensaje.svelte';

	let lista = $state([]);
	let grados = $state([]);
	let form = $state(null); // id = 0: registrar; id > 0: editar
	let error = $state('');
	let porRetirar = $state(null); // estudiante que se confirma en el Modal

	async function cargar() {
		try {
			lista = await listarEstudiantes();
		} catch (e) {
			avisar(e.message, true);
		}
	}
	onMount(async () => {
		cargar();
		grados = await listarGrados().catch(() => []);
	});

	const vacio = () => ({ id: 0, nombre: '', apellido: '', documento: '', id_grado: grados[0]?.id ?? '', nombre_acudiente: '', acudiente_autoriza: false });
	async function editar(s) {
		error = '';
		try {
			const e = await obtenerEstudiante(s.id); // datos actuales del servidor (el documento llega enmascarado)
			form = { id: e.id, nombre: e.nombre, apellido: e.apellido, documento: '', documentoActual: e.documento,
				id_grado: grados.find((g) => g.nombre === e.grado)?.id ?? '' };
		} catch (err) {
			avisar(err.message, true);
		}
	}
	async function guardar(ev) {
		ev.preventDefault();
		error = '';
		try {
			if (form.id) {
				// el documento solo se envia si se escribio uno nuevo; si no, el servidor conserva el actual
				const { nombre, apellido, documento } = form;
				await actualizarEstudiante(form.id, { nombre, apellido, id_grado: +form.id_grado, ...(documento ? { documento } : {}) });
				avisar('Estudiante actualizado');
			} else {
				const { id, ...nuevo } = form;
				await crearEstudiante({ ...nuevo, id_grado: +form.id_grado });
				avisar('Estudiante registrado');
			}
			form = null;
			cargar();
		} catch (e) {
			error = e.message; // ej. documento repetido (409) o grado invalido (422)
		}
	}
	async function retirar() {
		const s = porRetirar;
		porRetirar = null;
		try {
			await eliminarEstudiante(s.id);
			avisar('Estudiante retirado');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>Estudiantes | Conexión Escolar</title></svelte:head>

<Header titulo="Mis estudiantes" subtitulo="Solo tu colegio puede ver y editar esta lista." />
<div class="row"><Boton onclick={() => { error = ''; form = vacio(); }}>+ Registrar estudiante</Boton></div>
<Card class="tabla">
	<table>
		<thead><tr><th>Nombre</th><th>Documento</th><th>Grado</th><th></th></tr></thead>
		<tbody>
			{#each lista as s}
				<tr><td>{s.nombre} {s.apellido}</td><td>{s.documento}</td><td>{s.grado}</td><td><div class="row" style="margin:0;flex-wrap:nowrap"><Boton variante="borde" pequeno onclick={() => editar(s)}>Editar</Boton><Boton variante="borrar" pequeno onclick={() => (porRetirar = s)}>Retirar</Boton></div></td></tr>
			{:else}
				<SinDatos texto="Aún no has registrado estudiantes." columnas={4} />
			{/each}
		</tbody>
	</table>
</Card>
<p class="note">Solo se piden los datos mínimos necesarios. El documento se muestra enmascarado y los datos de menores se tratan según la <a href="/politica-de-privacidad">política de privacidad</a> (Ley 1581 de 2012).</p>

{#if form}
	<Modal titulo={form.id ? 'Editar estudiante' : 'Registrar estudiante'} cerrar={() => (form = null)}>
		<form onsubmit={guardar}>
			<CampoFormulario id="n" etiqueta="Nombre" required minlength="2" maxlength="100" bind:value={form.nombre} />
			<CampoFormulario id="a" etiqueta="Apellido" required minlength="2" maxlength="100" bind:value={form.apellido} />
			{#if form.id}
				<CampoFormulario id="d" etiqueta="Documento nuevo (opcional: déjalo vacío para conservar {form.documentoActual})" inputmode="numeric" pattern={'[0-9]{5,15}'} title="Entre 5 y 15 números" bind:value={form.documento} />
			{:else}
				<CampoFormulario id="d" etiqueta="Documento (solo números)" required inputmode="numeric" pattern={'[0-9]{5,15}'} title="Entre 5 y 15 números" bind:value={form.documento} />
			{/if}
			<label for="g">Grado</label>
			<select id="g" required bind:value={form.id_grado}>{#each grados as g}<option value={g.id}>{g.nombre}</option>{/each}</select>
			{#if !form.id}
				<CampoFormulario id="ac" etiqueta="Nombre del acudiente" required minlength="3" maxlength="150" bind:value={form.nombre_acudiente} />
				<label class="chk" style="margin-top:14px"><input type="checkbox" required bind:checked={form.acudiente_autoriza} />
					<span>Confirmo que el acudiente autorizó el tratamiento de los datos de este estudiante.</span></label>
			{/if}
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<div class="row" style="justify-content:flex-end;margin:16px 0 0">
				<Boton variante="borde" onclick={() => (form = null)}>Cancelar</Boton><Boton tipo="submit">Guardar</Boton>
			</div>
		</form>
	</Modal>
{/if}

{#if porRetirar}
	<Modal titulo="Retirar estudiante" cerrar={() => (porRetirar = null)}>
		<p>¿Retirar a <strong>{porRetirar.nombre} {porRetirar.apellido}</strong>? Se conserva su historial en los eventos.</p>
		<div class="row" style="justify-content:flex-end;margin:16px 0 0">
			<Boton variante="borde" onclick={() => (porRetirar = null)}>Cancelar</Boton><Boton variante="borrar" onclick={retirar}>Retirar</Boton>
		</div>
	</Modal>
{/if}
