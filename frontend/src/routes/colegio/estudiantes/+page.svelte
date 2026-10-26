<script>
	import { onMount } from 'svelte';
	import { listarEstudiantes, crearEstudiante, eliminarEstudiante } from '$lib/services/api_estudiante.js';
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
	let form = $state(null);
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

	const vacio = () => ({ nombre: '', apellido: '', documento: '', id_grado: grados[0]?.id ?? '', nombre_acudiente: '', acudiente_autoriza: false });
	async function guardar(ev) {
		ev.preventDefault();
		error = '';
		try {
			await crearEstudiante({ ...form, id_grado: +form.id_grado });
			form = null;
			avisar('Estudiante registrado');
			cargar();
		} catch (e) {
			error = e.message;
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
				<tr><td>{s.nombre} {s.apellido}</td><td>{s.documento}</td><td>{s.grado}</td><td><Boton variante="borrar" pequeno onclick={() => (porRetirar = s)}>Retirar</Boton></td></tr>
			{:else}
				<SinDatos texto="Aún no has registrado estudiantes." columnas={4} />
			{/each}
		</tbody>
	</table>
</Card>
<p class="note">Solo se piden los datos mínimos necesarios. El documento se muestra enmascarado y los datos de menores se tratan según la <a href="/politica-de-privacidad">política de privacidad</a> (Ley 1581 de 2012).</p>

{#if form}
	<Modal titulo="Registrar estudiante" cerrar={() => (form = null)}>
		<form onsubmit={guardar}>
			<CampoFormulario id="n" etiqueta="Nombre" required minlength="2" maxlength="100" bind:value={form.nombre} />
			<CampoFormulario id="a" etiqueta="Apellido" required minlength="2" maxlength="100" bind:value={form.apellido} />
			<CampoFormulario id="d" etiqueta="Documento (solo números)" required inputmode="numeric" pattern={'[0-9]{5,15}'} title="Entre 5 y 15 números" bind:value={form.documento} />
			<label for="g">Grado</label>
			<select id="g" required bind:value={form.id_grado}>{#each grados as g}<option value={g.id}>{g.nombre}</option>{/each}</select>
			<CampoFormulario id="ac" etiqueta="Nombre del acudiente" required minlength="3" maxlength="150" bind:value={form.nombre_acudiente} />
			<label class="chk" style="margin-top:14px"><input type="checkbox" required bind:checked={form.acudiente_autoriza} />
				<span>Confirmo que el acudiente autorizó el tratamiento de los datos de este estudiante.</span></label>
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
