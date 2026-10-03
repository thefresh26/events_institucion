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
	.velo { position: fixed; inset: 0; background: #0008; display: grid; place-items: center; z-index: 50; padding: 16px; }
	.caja { width: min(560px, 100%); max-height: 90vh; overflow: auto; outline: none; }
</style>
