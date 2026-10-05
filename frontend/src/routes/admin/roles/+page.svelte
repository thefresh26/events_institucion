<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/api.js';
	import { avisar } from '$lib/toast.svelte.js';

	const ROL = { administrador: 'Administrador', organizador: 'Organizador', colegio: 'Colegio' };
	const MOD = {
		panel: 'Panel', aprobar_eventos: 'Aprobar eventos', organizadores: 'Organizadores', colegios: 'Colegios', usuarios: 'Usuarios', roles: 'Roles y módulos',
		mis_eventos: 'Mis eventos', mis_colegios: 'Mis colegios', inscripciones: 'Inscripciones', asistencia: 'Asistencia', reportes: 'Reportes',
		eventos_disponibles: 'Eventos disponibles', mis_inscripciones: 'Mis inscripciones', mis_estudiantes: 'Estudiantes'
	};
	let roles = $state([]);
	let modulos = $state([]);
	let guardando = $state(0);

	onMount(async () => {
		try {
			const d = await api('/admin/roles');
			modulos = d.modulos;
			roles = d.roles.map((r) => ({ ...r, sel: new Set(r.modulos), original: r.modulos.join() }));
		} catch (e) {
			avisar(e.message, true);
		}
	});

	function alternar(r, id) {
		const s = new Set(r.sel);
		s.has(id) ? s.delete(id) : s.add(id);
		r.sel = s;
	}
	const cambiado = (r) => [...r.sel].sort((a, b) => a - b).join() !== r.original;

	async function guardar(r) {
		guardando = r.id;
		try {
			const res = await api(`/admin/roles/${r.id}/modulos`, { method: 'PUT', body: { modulos: [...r.sel] } });
			r.original = res.modulos.join();
			avisar(`Módulos de ${ROL[r.nombre] ?? r.nombre} guardados. Se aplican al volver a entrar.`);
		} catch (e) {
			avisar(e.message, true);
		}
		guardando = 0;
	}
</script>

<svelte:head><title>Roles | Conexión Escolar</title></svelte:head>

<h2>Roles y módulos</h2>
<p class="sub">Elige qué opciones del menú ve cada rol. El acceso a los datos lo sigue controlando el servidor según el rol.</p>

<div class="grid g2">
	{#each roles as r (r.id)}
		<div class="card">
			<h3>{ROL[r.nombre] ?? r.nombre}</h3>
			<p class="mut" style="margin:0 0 10px">{r.usuarios} {r.usuarios === 1 ? 'usuario' : 'usuarios'}{r.descripcion ? ' · ' + r.descripcion : ''}</p>
			{#each modulos as m (m.id)}
				<label class="chk">
					<input type="checkbox" checked={r.sel.has(m.id)} disabled={r.bloqueado} onchange={() => alternar(r, m.id)} />
					{MOD[m.nombre] ?? m.nombre}
				</label>
			{/each}
			{#if r.bloqueado}
				<p class="note">Los módulos del administrador no se pueden quitar: te quedarías sin acceso.</p>
			{:else}
				<div class="row" style="justify-content:flex-end;margin:12px 0 0">
					<button class="btn s" disabled={!cambiado(r) || guardando === r.id} onclick={() => guardar(r)}>{guardando === r.id ? 'Guardando…' : 'Guardar cambios'}</button>
				</div>
			{/if}
		</div>
	{/each}
</div>
