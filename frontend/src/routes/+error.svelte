<script>
	import { page } from '$app/stores';
</script>

<svelte:head><title>Página no encontrada | Eventos Escolares</title></svelte:head>

<div class="auth">
	<div class="card">
		<h1>{$page.status === 404 ? 'Página no encontrada' : 'Algo salió mal'}</h1>
		<p class="sub">La página que buscas no existe o fue movida.</p>
		<p><a class="btn" href="/">Volver al inicio</a></p>
	</div>
</div>
