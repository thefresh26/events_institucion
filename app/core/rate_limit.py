"""Limite de intentos de login (fuerza bruta). En memoria: suficiente para un
solo proceso. ponytail: si hay varios procesos, mover el contador a la base de datos."""
import threading
import time

MAX_INTENTOS = 5
VENTANA = 15 * 60  # segundos
_lock = threading.Lock()
_intentos: dict[str, tuple[int, float]] = {}


def segundos_de_bloqueo(clave: str) -> int:
    with _lock:
        r = _intentos.get(clave.lower())
        if not r:
            return 0
        n, t0 = r
        if time.time() - t0 >= VENTANA:
            del _intentos[clave.lower()]
            return 0
        return int(VENTANA - (time.time() - t0)) if n >= MAX_INTENTOS else 0


def registrar_fallo(clave: str) -> None:
    k = clave.lower()
    with _lock:
        n, t0 = _intentos.get(k, (0, time.time()))
        if time.time() - t0 >= VENTANA:
            n, t0 = 0, time.time()
        _intentos[k] = (n + 1, t0)


def limpiar(clave: str) -> None:
    with _lock:
        _intentos.pop(clave.lower(), None)
