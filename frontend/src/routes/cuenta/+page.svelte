<script>
	import { api } from '$lib/api.js';
	import { sesion } from '$lib/session.svelte.js';
	import { avisar } from '$lib/toast.svelte.js';

	let actual = $state('');
	let nueva = $state('');
	let error = $state('');

	async function cambiar(e) {
		e.preventDefault();
		error = '';
		try {
			await api('/auth/cambiar-contrasena', { method: 'POST', body: { actual, nueva } });
			actual = nueva = '';
			avisar('Contraseña actualizada');
		} catch (err) {
			error = err.message;
		}
	}
</script>

<svelte:head><title>Mi cuenta | Eventos Escolares</title></svelte:head>

<h2>Mi cuenta</h2>
<p class="sub">{sesion.usuario.correo} · {sesion.usuario.rol}</p>
<form class="card" style="max-width:440px" onsubmit={cambiar}>
	<h3>Cambiar contraseña</h3>
	<label for="a">Contraseña actual</label>
	<input id="a" type="password" required maxlength="72" autocomplete="current-password" bind:value={actual} />
	<label for="n">Nueva contraseña (8 o más, letras y números)</label>
	<input id="n" type="password" required minlength="8" maxlength="72" autocomplete="new-password" bind:value={nueva} />
	{#if error}<p class="err" role="alert">{error}</p>{/if}
	<p><button class="btn">Guardar</button></p>
</form>
