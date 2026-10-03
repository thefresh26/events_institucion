import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		// adapter-static genera archivos HTML/CSS/JS ya compilados (sin
		// servidor Node). El backend en FastAPI sirve esos archivos
		// directamente junto con la API, para que todo corra como un solo
		// servicio en Render. "fallback: 'index.html'" hace que cualquier
		// ruta (por ejemplo /registro) devuelva la misma página base y el
		// enrutador de SvelteKit se encargue del resto en el navegador (SPA).
		adapter: adapter({
			pages: 'build',
			assets: 'build',
			fallback: 'index.html',
			precompress: false,
			strict: true
		})
	}
};

export default config;
