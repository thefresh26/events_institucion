<script>
	import '../app.css';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { sesion, cargarSesion, salir } from '$lib/session.svelte.js';
	import { iniciarTema } from '$lib/tema.svelte.js';
	import Navbar from '$lib/components/Navbar.svelte';
	import Mensaje from '$lib/components/Mensaje.svelte';

	let { children } = $props();

	const PUBLICAS = ['/', '/login', '/registro', '/politica-de-privacidad', '/terminos'];
	// Menu segun los modulos que la base de datos le asigna al rol (tablas modulo y modulo_por_rol).
	const RUTAS = {
		panel: ['/panel', 'Panel'],
		aprobar_eventos: ['/admin/eventos', 'Eventos'],
		organizadores: ['/admin/organizadores', 'Organizadores'],
		colegios: ['/admin/colegios', 'Colegios'],
		usuarios: ['/admin/usuarios', 'Usuarios'],
		roles: ['/admin/roles', 'Roles'],
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

	onMount(() => {
		iniciarTema();
		cargarSesion();
	});

	$effect(() => {
		if (sesion.cargando) return;
		const ruta = $page.url.pathname;
		if (!sesion.usuario && !PUBLICAS.includes(ruta)) goto('/login');
		if (sesion.usuario && ['/', '/login', '/registro'].includes(ruta)) goto('/panel');
	});

	async function cerrarSesion() {
		await salir();
		window.location.assign('/login'); // recarga completa: no queda nada de la sesion anterior
	}
</script>

{#if sesion.cargando}
	<div class="centro mut" role="status"><div class="cargando"></div>Cargando…</div>
{:else if sesion.usuario && !['/login', '/registro'].includes($page.url.pathname)}
	<div class="app">
		<Navbar usuario={sesion.usuario} {menu} rutaActual={$page.url.pathname} onsalir={cerrarSesion} />
		<main>{@render children()}</main>
	</div>
{:else}
	<Navbar />
	{@render children()}
{/if}

<Mensaje />
