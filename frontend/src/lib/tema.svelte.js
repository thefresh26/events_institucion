export const tema = $state({ oscuro: false });

// app.html ya puso data-tema antes de pintar (sin parpadeo); aqui solo lo leemos.
export function iniciarTema() {
	tema.oscuro = document.documentElement.dataset.tema === 'dark';
}

export function alternarTema() {
	tema.oscuro = !tema.oscuro;
	document.documentElement.dataset.tema = tema.oscuro ? 'dark' : 'light';
	try { localStorage.setItem('tema', tema.oscuro ? 'dark' : 'light'); } catch {}
}
