"""INTEGRANTE 3: tablero de ataques.

Guarda lo que SABEMOS del tablero del rival. El programa no conoce sus barcos:
todo lo que hay aquí viene de lo que el rival nos dice ("agua", "tocado",
"hundido") tras cada disparo.
"""

import copy
from collections import deque

from constantes import (
    TAMANO, FLOTA, DESCONOCIDO, AGUA, TOCADO, HUNDIDO,
    RES_AGUA, RES_TOCADO, RES_HUNDIDO, RESULTADOS_VALIDOS,
)

_ORTOGONALES = ((-1, 0), (1, 0), (0, -1), (0, 1))


class TableroAtaques:
    def __init__(self, tamano=TAMANO, flota=None, barcos_pueden_tocarse=False):
        self.tamano = tamano
        self.flota = dict(flota if flota is not None else FLOTA)
        # Si es False, dos barcos nunca están en casillas contiguas (ni en diagonal).
        # Es la regla que permite deducir qué casillas son agua tras hundir un barco.
        self.barcos_pueden_tocarse = barcos_pueden_tocarse
        self.casillas = [[DESCONOCIDO] * tamano for _ in range(tamano)]
        self.hundidos = []  # tamaños de los barcos enemigos hundidos

    # ---------- consultas ----------
    def dentro(self, fila, col):
        return 0 <= fila < self.tamano and 0 <= col < self.tamano

    def estado(self, fila, col):
        return self.casillas[fila][col]

    @property
    def total_barcos(self):
        return sum(self.flota.values())

    def barcos_restantes(self):
        """Tamaños de los barcos enemigos que siguen a flote, de mayor a menor."""
        restantes = [t for t, n in self.flota.items() for _ in range(n)]
        for t in self.hundidos:
            if t in restantes:
                restantes.remove(t)
        return sorted(restantes, reverse=True)

    def todos_hundidos(self):
        return len(self.hundidos) >= self.total_barcos

    def tocados_sin_hundir(self):
        return [(f, c) for f in range(self.tamano) for c in range(self.tamano)
                if self.casillas[f][c] == TOCADO]

    def casillas_bloqueadas(self):
        """Casillas desconocidas que no pueden contener barco porque rodean a
        uno hundido (solo si los barcos no pueden tocarse)."""
        bloqueadas = set()
        if self.barcos_pueden_tocarse:
            return bloqueadas
        for f in range(self.tamano):
            for c in range(self.tamano):
                if self.casillas[f][c] != HUNDIDO:
                    continue
                for df in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        a, b = f + df, c + dc
                        if self.dentro(a, b) and self.casillas[a][b] == DESCONOCIDO:
                            bloqueadas.add((a, b))
        return bloqueadas

    # ---------- modificación ----------
    def registrar_disparo(self, fila, col, resultado):
        """Anota el resultado de un disparo nuestro.

        Devuelve la lista de casillas que han cambiado (varias si se hunde un
        barco, para que la interfaz las repinte todas).
        Lanza ValueError, sin modificar nada, si los datos no son válidos.
        """
        if resultado not in RESULTADOS_VALIDOS:
            raise ValueError(f"Resultado no válido: '{resultado}'")
        if not self.dentro(fila, col):
            raise ValueError(f"Coordenadas fuera del tablero: ({fila}, {col})")
        if self.casillas[fila][col] != DESCONOCIDO:
            raise ValueError("Esa casilla ya estaba registrada")

        if resultado == RES_AGUA:
            self.casillas[fila][col] = AGUA
            return [(fila, col)]
        if resultado == RES_TOCADO:
            self.casillas[fila][col] = TOCADO
            return [(fila, col)]

        # Hundido: todas las casillas tocadas conectadas pasan a hundidas
        self.casillas[fila][col] = TOCADO
        grupo = self._grupo_conectado(fila, col)
        for f, c in grupo:
            self.casillas[f][c] = HUNDIDO
        self.hundidos.append(len(grupo))
        return grupo

    def _grupo_conectado(self, fila, col):
        """Flood-fill (BFS) sobre casillas TOCADO contiguas en horizontal/vertical."""
        visto = {(fila, col)}
        cola = deque([(fila, col)])
        while cola:
            f, c = cola.popleft()
            for df, dc in _ORTOGONALES:
                a, b = f + df, c + dc
                if (a, b) not in visto and self.dentro(a, b) and self.casillas[a][b] == TOCADO:
                    visto.add((a, b))
                    cola.append((a, b))
        return sorted(visto)

    # ---------- guardado ----------
    def a_dict(self):
        return {
            "tamano": self.tamano,
            "flota": {str(k): v for k, v in self.flota.items()},
            "barcos_pueden_tocarse": self.barcos_pueden_tocarse,
            "casillas": copy.deepcopy(self.casillas),
            "hundidos": list(self.hundidos),
        }

    @classmethod
    def desde_dict(cls, datos):
        t = cls(datos["tamano"], {int(k): v for k, v in datos["flota"].items()},
                datos["barcos_pueden_tocarse"])
        t.casillas = copy.deepcopy(datos["casillas"])
        t.hundidos = list(datos["hundidos"])
        return t


if __name__ == "__main__":
    t = TableroAtaques()
    t.registrar_disparo(2, 2, RES_TOCADO)
    t.registrar_disparo(2, 3, RES_TOCADO)
    print(t.registrar_disparo(2, 4, RES_HUNDIDO))   # [(2,2), (2,3), (2,4)]
    print(t.barcos_restantes())
