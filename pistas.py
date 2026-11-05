"""
pistas.py
---------
Sistema de Radar IA: sugiere al jugador la mejor casilla para disparar.

Analiza las posiciones posibles de los barcos rivales que quedan a flote
y calcula un mapa de calor (probabilidad) para cada casilla desconocida.

Dos modos de funcionamiento:
- CAZA: no hay barcos tocados; busca la casilla con más probabilidad general.
- OBJETIVO: hay casillas tocadas sin hundir; prioriza las casillas adyacentes
  a los impactos existentes para rematar el barco.

DAM2 - Acceso a Datos - CES Juan Pablo II.
"""

import random
from constantes import DESCONOCIDO, TOCADO

MODO_CAZA = "caza"
MODO_OBJETIVO = "objetivo"


def modo(tablero):
    """Determina si estamos en modo objetivo (hay tocados pendientes) o modo caza."""
    return MODO_OBJETIVO if tablero.tocados_sin_hundir() else MODO_CAZA


def _libre(tablero, f, c, bloqueadas):
    """Una casilla es libre para un posible barco si es desconocida/tocada y no está bloqueada."""
    return tablero.estado(f, c) in (DESCONOCIDO, TOCADO) and (f, c) not in bloqueadas


def _colocaciones(tablero, tam, bloqueadas):
    """Genera todas las configuraciones posibles de tamaño `tam` en casillas válidas."""
    n = tablero.tamano
    for f in range(n):
        for c in range(n):
            for df, dc in ((0, 1), (1, 0)):
                if tam == 1 and (df, dc) == (1, 0):
                    continue  # Un barco de 1 casilla no necesita duplicar orientación
                celdas = [(f + i * df, c + i * dc) for i in range(tam)]
                if celdas[-1][0] >= n or celdas[-1][1] >= n:
                    continue
                if all(_libre(tablero, a, b, bloqueadas) for a, b in celdas):
                    yield celdas


def _acumular(tablero, exigir_tocado):
    """Calcula la matriz de calor sumando las combinaciones válidas para cada casilla."""
    n = tablero.tamano
    mapa = [[0] * n for _ in range(n)]
    bloqueadas = tablero.casillas_bloqueadas()
    tocados = set(tablero.tocados_sin_hundir())

    for tam in tablero.barcos_restantes():
        for celdas in _colocaciones(tablero, tam, bloqueadas):
            k = sum(1 for celda in celdas if celda in tocados)
            if exigir_tocado and k == 0:
                continue
            # En modo objetivo, las posiciones que cubren más tocados tienen mucho mayor peso
            peso = (k * k * 10) if exigir_tocado else 1
            for f, c in celdas:
                if tablero.estado(f, c) == DESCONOCIDO:
                    mapa[f][c] += peso
    return mapa


def mapa_probabilidades(tablero):
    """Devuelve la matriz con la puntuación de probabilidad para cada casilla del rival."""
    objetivo = bool(tablero.tocados_sin_hundir())
    mapa = _acumular(tablero, exigir_tocado=objetivo)
    # Si por alguna incongruencia el modo objetivo no encuentra hueco, volvemos a caza
    if objetivo and not any(any(fila) for fila in mapa):
        mapa = _acumular(tablero, exigir_tocado=False)
    return mapa


def _ranking(tablero, mapa, ignorar_bloqueadas=False):
    """Ordena las casillas desconocidas de mayor a menor probabilidad."""
    bloqueadas = set() if ignorar_bloqueadas else tablero.casillas_bloqueadas()
    cazando = modo(tablero) == MODO_CAZA
    ranking = []

    for f in range(tablero.tamano):
        for c in range(tablero.tamano):
            if tablero.estado(f, c) != DESCONOCIDO or (f, c) in bloqueadas:
                continue
            # Estrategia de tablero de ajedrez (paridad) en modo caza para barcos de tamaño >= 2
            paridad = 1 if cazando and (f + c) % 2 == 0 else 0
            ranking.append(((mapa[f][c], paridad), (f, c)))

    ranking.sort(key=lambda x: x[0], reverse=True)
    return ranking


def _ranking_valido(tablero, mapa):
    """Devuelve el ranking de casillas válidas para disparar."""
    ranking = _ranking(tablero, mapa)
    return ranking or _ranking(tablero, mapa, ignorar_bloqueadas=True)


def sugerir_casilla(tablero, rng=random):
    """Devuelve las coordenadas (fila, col) de la casilla más prometedora."""
    ranking = _ranking_valido(tablero, mapa_probabilidades(tablero))
    if not ranking:
        raise ValueError("No quedan casillas por disparar en el mapa del rival")
    mejor = ranking[0][0]
    candidatas = [pos for clave, pos in ranking if clave == mejor]
    return rng.choice(candidatas)


def pista(tablero, n_alternativas=3, rng=random):
    """
    Devuelve un diccionario completo de pista para la interfaz gráfica:
    - Modo ("caza" o "objetivo")
    - Casilla sugerida
    - Puntuación
    - Mapa de calor normalizado (0.0 a 1.0)
    """
    mapa = mapa_probabilidades(tablero)
    ranking = _ranking_valido(tablero, mapa)
    if not ranking:
        raise ValueError("No quedan casillas por disparar")

    mejor = ranking[0][0]
    casilla = rng.choice([pos for clave, pos in ranking if clave == mejor])
    maximo = max(max(fila) for fila in mapa)
    calor = [[(v / maximo if maximo > 0 else 0.0) for v in fila] for fila in mapa]
    alternativas = [pos for _, pos in ranking if pos != casilla][:n_alternativas]

    return {
        "modo": modo(tablero),
        "casilla": casilla,
        "puntuacion": mapa[casilla[0]][casilla[1]],
        "alternativas": alternativas,
        "mapa_calor": calor,
    }
