<script>
	import { goto } from '$app/navigation';
	import { iniciarSesion } from '$lib/services/api_auth.js';
	import { sesion } from '$lib/session.svelte.js';
	import Card from '$lib/components/Card.svelte';
	import CampoFormulario from '$lib/components/CampoFormulario.svelte';
	import Boton from '$lib/components/Boton.svelte';
	import Footer from '$lib/components/Footer.svelte';

	let correo = $state('');
	let contrasena = $state('');
	let error = $state('');
	let enviando = $state(false);

	async function entrar(e) {
		e.preventDefault();
		error = '';
		enviando = true;
		try {
			sesion.usuario = await iniciarSesion(correo, contrasena);
			goto('/panel');
		} catch (err) {
			error = err.message;
		}
		enviando = false;
	}
</script>

<svelte:head>
	<title>Iniciar sesión | Conexión Escolar</title>
	<meta name="description" content="Ingresa a la plataforma de eventos escolares como administrador, organizador o colegio." />
</svelte:head>

<div class="auth">
	<img class="auth-logo" src="/logo.png" alt="Conexión Escolar" width="230" height="157" />
	<Card>
		<form onsubmit={entrar}>
			<h1>Iniciar sesión</h1>
			<p class="sub">Ingresa con la cuenta de tu colegio u organización.</p>
			<CampoFormulario id="correo" etiqueta="Correo" tipo="email" autocomplete="username" required bind:value={correo} />
			<CampoFormulario id="clave" etiqueta="Contraseña" tipo="password" autocomplete="current-password" required maxlength="72" bind:value={contrasena} />
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<p><Boton tipo="submit" disabled={enviando}>{enviando ? 'Entrando…' : 'Entrar'}</Boton></p>
			<p class="mut">¿Eres organizador y aún no tienes cuenta? <a href="/registro">Regístrate</a>. Los colegios reciben su acceso del organizador.</p>
			<Footer><a href="/politica-de-privacidad">Privacidad</a><a href="/terminos">Términos</a></Footer>
		</form>
	</Card>
</div>
