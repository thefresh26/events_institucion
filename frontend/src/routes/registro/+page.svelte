<script>
	import { api } from '$lib/api.js';

	let f = $state({ correo: '', contrasena: '', nombre: '', apellido: '', organizacion_nombre: '', nit: '', telefono: '', descripcion: '' });
	let sitioWeb = $state(''); // honeypot: las personas no lo ven; los bots suelen llenarlo
	let acepto = $state(false);
	let error = $state('');
	let listo = $state(false);
	let enviando = $state(false);

	async function enviar(e) {
		e.preventDefault();
		error = '';
		if (sitioWeb) return (listo = true); // bot: simulamos exito y no enviamos nada
		enviando = true;
		const cuerpo = Object.fromEntries(Object.entries(f).filter(([, v]) => v !== ''));
		try {
			await api('/auth/registro/organizador', { method: 'POST', body: cuerpo });
			listo = true;
		} catch (err) {
			error = err.message;
		}
		enviando = false;
	}
</script>

<svelte:head>
	<title>Registrar organización | Eventos Escolares</title>
	<meta name="description" content="Registra tu organización para crear eventos escolares e invitar a colegios a participar." />
</svelte:head>

<div class="auth">
	{#if listo}
		<div class="card" role="status">
			<h1>Registro recibido</h1>
			<p>Un administrador revisará tu organización. Cuando la apruebe podrás iniciar sesión.</p>
			<p><a class="btn" href="/login">Ir a iniciar sesión</a></p>
		</div>
	{:else}
		<form class="card" onsubmit={enviar}>
			<h1>Registrar organización</h1>
			<p class="sub">Para quienes crean eventos. Los colegios los registra el organizador.</p>
			<label for="org">Nombre de la organización</label>
			<input id="org" required minlength="3" maxlength="150" bind:value={f.organizacion_nombre} />
			<label for="nit">NIT</label>
			<input id="nit" required inputmode="numeric" pattern="[0-9\-]{'{5,20}'}" title="Solo números y guion" bind:value={f.nit} />
			<label for="nom">Nombre de contacto</label>
			<input id="nom" required minlength="2" maxlength="100" autocomplete="given-name" bind:value={f.nombre} />
			<label for="ape">Apellido de contacto</label>
			<input id="ape" required minlength="2" maxlength="100" autocomplete="family-name" bind:value={f.apellido} />
			<label for="tel">Teléfono (opcional)</label>
			<input id="tel" type="tel" maxlength="20" autocomplete="tel" bind:value={f.telefono} />
			<label for="mail">Correo</label>
			<input id="mail" type="email" required autocomplete="email" bind:value={f.correo} />
			<label for="pw">Contraseña (8 o más, con letras y números)</label>
			<input id="pw" type="password" required minlength="8" maxlength="72" autocomplete="new-password" bind:value={f.contrasena} />
			<div style="position:absolute;left:-9999px" aria-hidden="true">
				<label for="web">No llenar</label>
				<input id="web" tabindex="-1" autocomplete="off" bind:value={sitioWeb} />
			</div>
			<label class="chk" style="margin-top:14px">
				<input type="checkbox" required bind:checked={acepto} />
				<span>Acepto la <a href="/politica-de-privacidad" target="_blank" rel="noopener">política de privacidad</a> y los <a href="/terminos" target="_blank" rel="noopener">términos</a>.</span>
			</label>
			{#if error}<p class="err" role="alert">{error}</p>{/if}
			<p><button class="btn" disabled={enviando || !acepto}>{enviando ? 'Enviando…' : 'Enviar registro'}</button></p>
			<p class="mut"><a href="/login">Ya tengo cuenta</a></p>
		</form>
	{/if}
</div>
