<script>
	// Etiqueta + campo. Lo demas (required, min, max, autocomplete, maxlength...) pasa directo al <input>.
	let { id, etiqueta, tipo = 'text', placeholder = '', value = $bindable(''), ...resto } = $props();
</script>

<label for={id}>{etiqueta}</label>
<input {id} type={tipo} {placeholder} bind:value {...resto} />
