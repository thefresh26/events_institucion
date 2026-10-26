<script>
	import { cambiarContrasena } from '$lib/services/api_auth.js';
	import { sesion } from '$lib/session.svelte.js';
	import Header from '$lib/components/Header.svelte';
	import Card from '$lib/components/Card.svelte';
	import CampoFormulario from '$lib/components/CampoFormulario.svelte';
	import Boton from '$lib/components/Boton.svelte';
	import { avisar } from '$lib/components/Mensaje.svelte';

	let actual = $state('');
	let nueva = $state('');
	let error = $state('');

	async function cambiar(e) {
		e.preventDefault();
		error = '';
		try {
			await cambiarContrasena(actual, nueva);
			actual = nueva = '';
			avisar('Contraseña actualizada');
		} catch (err) {
			error = err.message;
		}
	}
</script>

<svelte:head><title>Mi cuenta | Conexión Escolar</title></svelte:head>

<Header titulo="Mi cuenta" subtitulo="{sesion.usuario.correo} · {sesion.usuario.rol}" />
<Card style="max-width:440px">
	<form onsubmit={cambiar}>
		<h3>Cambiar contraseña</h3>
		<CampoFormulario id="a" etiqueta="Contraseña actual" tipo="password" required maxlength="72" autocomplete="current-password" bind:value={actual} />
		<CampoFormulario id="n" etiqueta="Nueva contraseña (8 o más, letras y números)" tipo="password" required minlength="8" maxlength="72" autocomplete="new-password" bind:value={nueva} />
		{#if error}<p class="err" role="alert">{error}</p>{/if}
		<p><Boton tipo="submit">Guardar</Boton></p>
	</form>
</Card>
