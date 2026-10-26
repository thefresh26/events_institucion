<script>
	import { onMount } from 'svelte';
	let { titulo, cerrar, children } = $props();
	let caja;
	onMount(() => {
		caja?.focus();
		const previo = document.activeElement;
		return () => previo?.focus?.();
	});
</script>

<svelte:window onkeydown={(e) => e.key === 'Escape' && cerrar()} />
<div class="velo" role="presentation" onclick={(e) => e.target === e.currentTarget && cerrar()}>
	<div class="caja card" role="dialog" aria-modal="true" aria-label={titulo} tabindex="-1" bind:this={caja}>
		<h2>{titulo}</h2>
		{@render children()}
	</div>
</div>

<style>
	.velo { position: fixed; inset: 0; background: #0a1a1299; backdrop-filter: blur(5px); display: grid; place-items: center; z-index: 50; padding: 16px; animation: velo .25s ease both; }
	.caja { width: min(580px, 100%); max-height: 90vh; overflow: auto; outline: none; border-radius: 22px; padding: 26px; box-shadow: 0 40px 80px -30px #000a; animation: pop .4s cubic-bezier(.22, 1, .36, 1) both; }
	@keyframes velo { from { opacity: 0; } to { opacity: 1; } }
	@media (prefers-reduced-motion: reduce) { .velo, .caja { animation: none; } }
</style>
