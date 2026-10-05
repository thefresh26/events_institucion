<script>
	import { tema, alternarTema } from '$lib/tema.svelte.js';
	let { flota = false } = $props();
</script>

<button class="tema-btn" class:tema-flota={flota} onclick={alternarTema} aria-pressed={tema.oscuro} aria-label={tema.oscuro ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'} title={tema.oscuro ? 'Modo claro' : 'Modo oscuro'}>
	{#if tema.oscuro}
		<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
		<span>Modo claro</span>
	{:else}
		<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
		<span>Modo oscuro</span>
	{/if}
</button>
