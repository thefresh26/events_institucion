<script>
	import { goto } from '$app/navigation';
	import { api } from '$lib/api.js';
	import { sesion } from '$lib/session.svelte.js';

	let correo = $state('');
	let contrasena = $state('');
	let error = $state('');
	let enviando = $state(false);

	async function entrar(e) {
		e.preventDefault();
		error = '';
		enviando = true;
		try {
			sesion.usuario = await api('/auth/login', { method: 'POST', body: { correo, contrasena } });
			goto('/panel');
		} catch (err) {
			error = err.message;
		}
		enviando = false;
	}
</script>

<svelte:head>
	<title>Iniciar sesión | Eventos Escolares</title>
	<meta name="description" content="Ingresa a la plataforma de eventos escolares como administrador, organizador o colegio." />
</svelte:head>

<div class="auth">
	<form class="card" onsubmit={entrar}>
		<h1>Iniciar sesión</h1>
		<p class="sub">Ingresa con la cuenta de tu colegio u organización.</p>
		<label for="correo">Correo</label>
		<input id="correo" type="email" autocomplete="username" required bind:value={correo} />
		<label for="clave">Contraseña</label>
		<input id="clave" type="password" autocomplete="current-password" required maxlength="72" bind:value={contrasena} />
		{#if error}<p class="err" role="alert">{error}</p>{/if}
		<p><button class="btn" disabled={enviando}>{enviando ? 'Entrando…' : 'Entrar'}</button></p>
		<p class="mut">¿Eres organizador y aún no tienes cuenta? <a href="/registro">Regístrate</a>. Los colegios reciben su acceso del organizador.</p>
		<p class="pie"><a href="/politica-de-privacidad">Privacidad</a><a href="/terminos">Términos</a></p>
	</form>
</div>
