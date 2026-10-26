<script>
	// Titulo de cada pagina. Sin envoltorio: app.css decora "main > h2:first-child" (raya dorada) y ".sub".
	let { titulo, subtitulo = '' } = $props();
</script>

<h2>{titulo}</h2>
{#if subtitulo}
	<p class="sub">{subtitulo}</p>
{/if}
