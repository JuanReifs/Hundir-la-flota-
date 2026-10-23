"""INTEGRANTE 3: pistas.

No es IA real: es un cálculo de probabilidades. Para cada barco enemigo que
sigue a flote se prueba cada posición posible (horizontal y vertical) y se
suma +1 a cada casilla que cubre. La casilla con más puntos es la más probable.

- Modo CAZA: no hay tocados pendientes. Se puntúan todas las posiciones válidas.
- Modo OBJETIVO: hay tocados sin hundir. Solo cuentan las posiciones que pasan
  por algún tocado (y pesan más cuantos más tocados cubren), así que la pista
  prolonga la línea cuando ya hay dos tocados seguidos.
"""

import random

from constantes import DESCONOCIDO, TOCADO

MODO_CAZA = "caza"
MODO_OBJETIVO = "objetivo"


def modo(tablero):
    return MODO_OBJETIVO if tablero.tocados_sin_hundir() else MODO_CAZA


def _libre(tablero, f, c, bloqueadas):
    return tablero.estado(f, c) in (DESCONOCIDO, TOCADO) and (f, c) not in bloqueadas


def _colocaciones(tablero, tam, bloqueadas):
    """Genera todas las listas de casillas donde cabría un barco de tamaño `tam`."""
    n = tablero.tamano
    for f in range(n):
        for c in range(n):
            for df, dc in ((0, 1), (1, 0)):
                if tam == 1 and (df, dc) == (1, 0):
                    continue  # un barco de 1 casilla no tiene orientación
                celdas = [(f + i * df, c + i * dc) for i in range(tam)]
                if celdas[-1][0] >= n or celdas[-1][1] >= n:
                    continue
                if all(_libre(tablero, a, b, bloqueadas) for a, b in celdas):
                    yield celdas


def _acumular(tablero, exigir_tocado):
    n = tablero.tamano
    mapa = [[0] * n for _ in range(n)]
    bloqueadas = tablero.casillas_bloqueadas()
    tocados = set(tablero.tocados_sin_hundir())
    for tam in tablero.barcos_restantes():
        for celdas in _colocaciones(tablero, tam, bloqueadas):
            k = sum(1 for celda in celdas if celda in tocados)
            if exigir_tocado and k == 0:
                continue
            peso = k * k if exigir_tocado else 1
            for f, c in celdas:
                if tablero.estado(f, c) == DESCONOCIDO:
                    mapa[f][c] += peso
    return mapa


def mapa_probabilidades(tablero):
    """Matriz con la puntuación de cada casilla (0 en las ya disparadas)."""
    objetivo = bool(tablero.tocados_sin_hundir())
    mapa = _acumular(tablero, exigir_tocado=objetivo)
    if objetivo and not any(any(fila) for fila in mapa):
        mapa = _acumular(tablero, exigir_tocado=False)  # datos incoherentes: no bloquearse
    return mapa


def _ranking(tablero, mapa, ignorar_bloqueadas=False):
    bloqueadas = set() if ignorar_bloqueadas else tablero.casillas_bloqueadas()
    cazando = modo(tablero) == MODO_CAZA
    ranking = []
    for f in range(tablero.tamano):
        for c in range(tablero.tamano):
            if tablero.estado(f, c) != DESCONOCIDO or (f, c) in bloqueadas:
                continue
            paridad = 1 if cazando and (f + c) % 2 == 0 else 0  # desempate: tablero de ajedrez
            ranking.append(((mapa[f][c], paridad), (f, c)))
    ranking.sort(key=lambda x: x[0], reverse=True)
    return ranking


def _ranking_valido(tablero, mapa):
    ranking = _ranking(tablero, mapa)
    return ranking or _ranking(tablero, mapa, ignorar_bloqueadas=True)


def sugerir_casilla(tablero, rng=random):
    """Devuelve (fila, col) de la casilla más recomendable.
    Lanza ValueError si no queda ninguna casilla por disparar."""
    ranking = _ranking_valido(tablero, mapa_probabilidades(tablero))
    if not ranking:
        raise ValueError("No quedan casillas por disparar")
    mejor = ranking[0][0]
    return rng.choice([pos for clave, pos in ranking if clave == mejor])


def pista(tablero, n_alternativas=3, rng=random):
    """Pista completa para la interfaz.

    {"modo": "caza"|"objetivo", "casilla": (f, c), "puntuacion": int,
     "alternativas": [(f, c), ...], "mapa_calor": matriz con valores de 0 a 1}
    """
    mapa = mapa_probabilidades(tablero)
    ranking = _ranking_valido(tablero, mapa)
    if not ranking:
        raise ValueError("No quedan casillas por disparar")
    mejor = ranking[0][0]
    casilla = rng.choice([pos for clave, pos in ranking if clave == mejor])
    maximo = max(max(fila) for fila in mapa)
    calor = [[(v / maximo if maximo else 0.0) for v in fila] for fila in mapa]
    alternativas = [pos for _, pos in ranking if pos != casilla][:n_alternativas]
    return {
        "modo": modo(tablero),
        "casilla": casilla,
        "puntuacion": mapa[casilla[0]][casilla[1]],
        "alternativas": alternativas,
        "mapa_calor": calor,
    }


if __name__ == "__main__":
    from ataques import TableroAtaques
    from constantes import RES_TOCADO, coord_a_texto
    t = TableroAtaques()
    print("Caza:", pista(t)["casilla"])
    t.registrar_disparo(5, 5, RES_TOCADO)
    t.registrar_disparo(5, 6, RES_TOCADO)
    p = pista(t)
    print(p["modo"], coord_a_texto(*p["casilla"]))  # prolonga la línea
