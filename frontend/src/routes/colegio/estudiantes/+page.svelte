<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api.js';
	import Modal from '$lib/Modal.svelte';
	import { avisar } from '$lib/toast.svelte.js';

	let lista = $state([]);
	let grados = $state([]);
	let form = $state(null);
	let error = $state('');

	async function cargar() {
		try {
			lista = await api('/colegio/estudiantes');
		} catch (e) {
			avisar(e.message, true);
		}
	}
	onMount(async () => {
		cargar();
		grados = await api('/catalogos/grados').catch(() => []);
	});

	const vacio = () => ({ nombre: '', apellido: '', documento: '', id_grado: grados[0]?.id ?? '', nombre_acudiente: '', acudiente_autoriza: false });
	async function guardar(ev) {
		ev.preventDefault();
		error = '';
		try {
			await api('/colegio/estudiantes', { method: 'POST', body: { ...form, id_grado: +form.id_grado } });
			form = null;
			avisar('Estudiante registrado');
			cargar();
		} catch (e) {
			error = e.message;
		}
	}
	async function retirar(s) {
		if (!confirm(`¿Retirar a ${s.nombre} ${s.apellido}? Se conserva su historial en los eventos.`)) return;
		try {
			await api(`/colegio/estudiantes/${s.id}`, { method: 'DELETE' });
			avisar('Estudiante retirado');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>Estudiantes | Conexión Escolar</title></svelte:head>

<h2>Mis estudiantes</h2>
<p class="sub">Solo tu colegio puede ver y editar esta lista.</p>
<div class="row"><button class="btn" onclick={() => { error = ''; form = vacio(); }}>+ Registrar estudiante</button></div>
<div class="card tabla">
	<table>
		<thead><tr><th>Nombre</th><th>Documento</th><th>Grado</th><th></th></tr></thead>
		<tbody>
			{#each lista as s}
				<tr><td>{s.nombre} {s.apellido}</td><td>{s.documento}</td><td>{s.grado}</td><td><button class="btn r s" onclick={() => retirar(s)}>Retirar</button></td></tr>
			{:else}
				<tr><td colspan="4" class="mut">Aún no has registrado estudiantes.</td></tr>
			{/each}
		</tbody>
	</table>
</div>
<p class="note">Solo se piden los datos mínimos necesarios. El documento se muestra enmascarado y los datos de menores se tratan según la <a href="/politica-de-privacidad">política de privacidad</a> (Ley 1581 de 2012).</p>

{#if form}
	<Modal titulo="Registrar estudiante" cerrar={() => (form = null)}>
		<form onsubmit={guardar}>
			<label for="n">Nombre</label><input id="n" required minlength="2" maxlength="100" bind:value={form.nombre} />
			<label for="a">Apellido</label><input id="a" required minlength="2" maxlength="100" bind:value={form.apellido} />
			<label for="d">Documento (solo números)</label><input id="d" required inputmode="numeric" pattern="[0-9]{'{5,15}'}" title="Entre 5 y 15 números" bind:value={form.documento} />
			<label for="g">Grado</label>
			<select id="g" required bind:value={form.id_grado}>{#each grados as g}<option value={g.id}>{g.nombre}</option>{/each}</select>
			<label for="ac">Nombre del acudiente</label><input id="ac" required minlength="3" maxlength="150" bind:value={form.nombre_acudiente} />
			<label class="chk" style="margin-top:14px"><input type="checkbox" required bind:checked={form.acudiente_autoriza} />
				<span>Confirmo que el acudiente autorizó el tratamiento de los datos de este estudiante.</span></label>
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<div class="row" style="justify-content:flex-end;margin:16px 0 0">
				<button type="button" class="btn o" onclick={() => (form = null)}>Cancelar</button><button class="btn">Guardar</button>
			</div>
		</form>
	</Modal>
{/if}
