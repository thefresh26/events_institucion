<script>
	// Tabla con buscador, orden por columna, filas por pagina y paginacion, hecha con la libreria
	// @vincjo/datatables (DataTable para Svelte 5). Es reutilizable: cada pagina solo le pasa
	//   filas    = el arreglo de datos
	//   columnas = [{ t: 'Titulo', k: 'campo' o (fila) => valor }]   (sin k = columna sin orden, ej. acciones)
	//   fila     = snippet que dibuja los <td> de una fila (asi los botones y componentes siguen funcionando)
	import { TableHandler, Datatable, ThSort, Th } from '@vincjo/datatables';
	import SinDatos from '$lib/components/SinDatos.svelte';

	let { filas = [], columnas = [], fila, vacio = 'No hay datos para mostrar.', porPagina = 10 } = $props();

	const es = {
		search: 'Buscar...',
		show: 'Mostrar',
		entries: 'registros',
		filter: 'Filtrar',
		rowCount: 'Mostrando {start} a {end} de {total} registros',
		noRows: 'No se encontraron registros',
		previous: 'Anterior',
		next: 'Siguiente'
	};
	const table = new TableHandler([], { rowsPerPage: porPagina, i18n: es });
	$effect(() => table.setRows(filas));
</script>

<div class="tabla-datos">
<Datatable {table} basic>
	<table>
		<thead>
			<tr>
				{#each columnas as c}
					{#if c.k}<ThSort {table} field={c.k}>{c.t}</ThSort>{:else}<Th>{c.t}</Th>{/if}
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each table.rows as f}
				{@render fila(f)}
			{:else}
				<SinDatos texto={vacio} columnas={columnas.length} />
			{/each}
		</tbody>
	</table>
</Datatable>
</div>

<style>
	.tabla-datos { overflow-x: auto; }
	/* app.css da estilo de menu lateral a todo <aside>; aqui se anula para los <aside> de la libreria (filas por pagina y conteo) */
	.tabla-datos :global(section header aside), .tabla-datos :global(section footer aside) {
		width: auto; height: auto; position: static; display: flex; flex-direction: row; gap: 0;
		background: none; color: var(--mut); padding: 0; line-height: 32px; margin: 8px 16px;
	}
	.tabla-datos :global(section header aside) { align-items: center; }
	.tabla-datos :global(section footer aside) { display: block; }
	.tabla-datos :global(select), .tabla-datos :global(input) { width: auto; }
	.tabla-datos :global(footer) { padding-bottom: 6px; }
</style>
