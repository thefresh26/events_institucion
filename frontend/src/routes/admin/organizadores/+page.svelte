<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api.js';
	import { avisar } from '$lib/toast.svelte.js';

	let lista = $state([]);
	async function cargar() {
		try {
			lista = await api('/admin/organizadores');
		} catch (e) {
			avisar(e.message, true);
		}
	}
	onMount(cargar);

	async function activar(o, activo) {
		try {
			await api(`/admin/organizadores/${o.id}/activo`, { method: 'PATCH', body: { activo } });
			avisar(activo ? 'Organizador aprobado' : 'Organizador desactivado');
			cargar();
		} catch (e) {
			avisar(e.message, true);
		}
	}
</script>

<svelte:head><title>Organizadores | Eventos Escolares</title></svelte:head>

<h2>Organizadores</h2>
<p class="sub">Aprueba las cuentas nuevas antes de que puedan crear eventos.</p>
<div class="card tabla">
	<table>
		<thead><tr><th>Organización</th><th>NIT</th><th>Correo</th><th>Teléfono</th><th>Estado</th><th></th></tr></thead>
		<tbody>
			{#each lista as o}
				<tr>
					<td><strong>{o.nombre}</strong></td><td>{o.nit}</td><td>{o.correo}</td><td>{o.telefono ?? ''}</td>
					<td><span class="b {o.activo ? 'publicado' : 'pendiente'}">{o.activo ? 'Activo' : 'Pendiente / inactivo'}</span></td>
					<td>
						{#if o.activo}
							<button class="btn o s" onclick={() => activar(o, false)}>Desactivar</button>
						{:else}
							<button class="btn s" onclick={() => activar(o, true)}>Aprobar</button>
						{/if}
					</td>
				</tr>
			{:else}
				<tr><td colspan="6" class="mut">Aún no hay organizadores registrados.</td></tr>
			{/each}
		</tbody>
	</table>
</div>
