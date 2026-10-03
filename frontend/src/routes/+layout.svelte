<script>
	import '../app.css';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { sesion, cargarSesion, salir } from '$lib/session.svelte.js';
	import { aviso } from '$lib/toast.svelte.js';

	let { children } = $props();

	const PUBLICAS = ['/', '/login', '/registro', '/politica-de-privacidad', '/terminos'];
	// Menu segun los modulos que la base de datos le asigna al rol (tablas modulo y modulo_por_rol).
	const RUTAS = {
		panel: ['/panel', 'Panel'],
		aprobar_eventos: ['/admin/eventos', 'Eventos'],
		organizadores: ['/admin/organizadores', 'Organizadores'],
		colegios: ['/admin/colegios', 'Colegios'],
		mis_eventos: ['/organizador/eventos', 'Mis eventos'],
		mis_colegios: ['/organizador/colegios', 'Mis colegios'],
		inscripciones: ['/organizador/inscripciones', 'Inscripciones'],
		asistencia: ['/organizador/asistencia', 'Asistencia'],
		reportes: ['/organizador/reportes', 'Reportes'],
		eventos_disponibles: ['/colegio/eventos', 'Eventos'],
		mis_inscripciones: ['/colegio/inscripciones', 'Mis inscripciones'],
		mis_estudiantes: ['/colegio/estudiantes', 'Estudiantes']
	};
	const menu = $derived(
		Object.entries(RUTAS).filter(([k]) => sesion.usuario?.modulos.includes(k)).map(([, v]) => v)
	);

	onMount(cargarSesion);

	$effect(() => {
		if (sesion.cargando) return;
		const ruta = $page.url.pathname;
		if (!sesion.usuario && !PUBLICAS.includes(ruta)) goto('/login');
		if (sesion.usuario && ['/', '/login', '/registro'].includes(ruta)) goto('/panel');
	});

	async function cerrarSesion() {
		await salir();
		goto('/login');
	}
</script>

{#if sesion.cargando}
	<p class="centro mut" role="status">Cargando…</p>
{:else if sesion.usuario}
	<div class="app">
		<aside>
			<h1><span class="logo">E</span>Eventos Escolares</h1>
			<nav aria-label="Principal">
				{#each menu as [ruta, nombre]}
					<a class="nav" class:on={$page.url.pathname.startsWith(ruta)} href={ruta}>{nombre}</a>
				{/each}
			</nav>
			<div class="who">
				<strong>{sesion.usuario.nombre} {sesion.usuario.apellido}</strong>
				<span>{sesion.usuario.rol}</span>
				<a href="/cuenta">Mi cuenta</a>
				<button class="btn o s" onclick={cerrarSesion}>Cerrar sesión</button>
			</div>
		</aside>
		<main>{@render children()}</main>
	</div>
{:else}
	{@render children()}
{/if}

{#if aviso.texto}
	<div class="toast" class:error={aviso.error} role="status">{aviso.texto}</div>
{/if}
