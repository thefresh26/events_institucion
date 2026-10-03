import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// En desarrollo, /api se reenvia al backend (uvicorn en el puerto 8000).
export default defineConfig({
	plugins: [sveltekit()],
	server: { proxy: { '/api': 'http://localhost:8000' } }
});
