"""
ataques.py
----------
Tablero de ataques realizados al rival (mapa de nuestros disparos).

Este módulo se encarga de:
- Registrar los resultados (agua, tocado, hundido) que el rival nos comunica.
- Llevar la cuenta de los barcos enemigos hundidos y los que quedan a flote.
- Detectar casillas tocadas sin hundir para el radar IA.

REGLA ESTRICTA (exigida por el enunciado y por el usuario):
- SIN propagación automática (sin flood-fill ni autocompletado en cadena).
- Cada casilla se marca individualmente. Esto evita que barcos contiguos
  (por ejemplo formando una 'L') se marquen erróneamente como hundidos.

DAM2 - Acceso a Datos - CES Juan Pablo II.
"""

import copy
from constantes import (
    TAMANO,
    CONFIGURACION_FLOTA,
    DESCONOCIDO,
    AGUA,
    TOCADO,
    HUNDIDO,
    RES_AGUA,
    RES_TOCADO,
    RES_HUNDIDO,
    RESULTADOS_VALIDOS,
)

_ORTOGONALES = ((-1, 0), (1, 0), (0, -1), (0, 1))


class TableroAtaques:
    """Representa el mapa de los disparos que realizamos contra la flota rival."""

    def __init__(self, tamano=TAMANO, flota=None, barcos_pueden_tocarse=True):
        self.tamano = tamano
        self.flota = dict(flota if flota is not None else CONFIGURACION_FLOTA)
        self.barcos_pueden_tocarse = barcos_pueden_tocarse
        # Matriz 10x10: 0=DESCONOCIDO, 1=AGUA, 2=TOCADO, 3=HUNDIDO
        self.casillas = [[DESCONOCIDO] * tamano for _ in range(tamano)]

    def dentro(self, fila, col):
        """Comprueba si una casilla está dentro de las dimensiones del tablero."""
        return 0 <= fila < self.tamano and 0 <= col < self.tamano

    def estado(self, fila, col):
        """Devuelve el estado de la casilla: DESCONOCIDO, AGUA, TOCADO o HUNDIDO."""
        return self.casillas[fila][col]

    @property
    def total_barcos(self):
        """Número total de barcos que posee la flota enemiga."""
        return sum(self.flota.values())

    @property
    def total_celdas_flota(self):
        """Total de casillas ocupadas por la flota (1x4 + 2x3 + 3x2 + 4x1 = 20)."""
        return sum(tam * cant for tam, cant in self.flota.items())

    def celdas_hundidas(self):
        """Cuenta el total de casillas marcadas como HUNDIDO."""
        return sum(
            1
            for f in range(self.tamano)
            for c in range(self.tamano)
            if self.casillas[f][c] == HUNDIDO
        )

    def todos_hundidos(self):
        """Devuelve True si se han marcado todas las casillas de la flota enemiga como hundidas."""
        return self.celdas_hundidas() >= self.total_celdas_flota

    @property
    def hundidos(self):
        """
        Lista con los tamaños de los barcos enemigos completados (hundidos).
        Agrupa casillas contiguas marcadas como HUNDIDO para deducir tamaños completados.
        """
        vistos = set()
        barcos_hundidos = []

        for f in range(self.tamano):
            for c in range(self.tamano):
                if self.casillas[f][c] == HUNDIDO and (f, c) not in vistos:
                    # BFS para medir el tamaño de este grupo hundido
                    grupo = [(f, c)]
                    vistos.add((f, c))
                    idx = 0
                    while idx < len(grupo):
                        gf, gc = grupo[idx]
                        idx += 1
                        for df, dc in _ORTOGONALES:
                            af, ac = gf + df, gc + dc
                            if (
                                self.dentro(af, ac)
                                and (af, ac) not in vistos
                                and self.casillas[af][ac] == HUNDIDO
                            ):
                                vistos.add((af, ac))
                                grupo.append((af, ac))
                    barcos_hundidos.append(len(grupo))

        return barcos_hundidos

    def barcos_restantes(self):
        """Devuelve los tamaños de los barcos enemigos que siguen a flote."""
        restantes = [t for t, n in self.flota.items() for _ in range(n)]
        for t in self.hundidos:
            if t in restantes:
                restantes.remove(t)
        return sorted(restantes, reverse=True)

    def tocados_sin_hundir(self):
        """Devuelve las casillas (fila, col) con impactos 'TOCADO' que aún no se han marcado como hundidas."""
        return [
            (f, c)
            for f in range(self.tamano)
            for c in range(self.tamano)
            if self.casillas[f][c] == TOCADO
        ]

    def casillas_bloqueadas(self):
        """Casillas desconocidas que no pueden tener barco (si no se tocan)."""
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

    def registrar_disparo(self, fila, col, resultado):
        """
        Anota el resultado devuelto por el rival para la casilla (fila, col).
        
        REGLA CLAVE: NUNCA propaga automáticamente a casillas vecinas.
        Modifica ÚNICAMENTE la coordenada indicada por el jugador.
        Permite cambiar una casilla previamente 'TOCADO' a 'HUNDIDO'.
        """
        if resultado not in RESULTADOS_VALIDOS:
            raise ValueError(f"Resultado no válido: '{resultado}' (debe ser agua, tocado o hundido)")

        if not self.dentro(fila, col):
            raise ValueError(f"Coordenadas fuera del tablero: ({fila}, {col})")

        estado_actual = self.casillas[fila][col]

        # Validaciones de cambio de estado
        if estado_actual == HUNDIDO and resultado == RES_HUNDIDO:
            raise ValueError(f"La casilla ({fila}, {col}) ya estaba registrada como HUNDIDA")
        if estado_actual == AGUA and resultado == RES_AGUA:
            raise ValueError(f"La casilla ({fila}, {col}) ya estaba registrada como AGUA")
        if estado_actual == TOCADO and resultado == RES_TOCADO:
            raise ValueError(f"La casilla ({fila}, {col}) ya estaba registrada como TOCADO")

        # Asignación estrictamente individual (sin flood-fill ni propagación)
        if resultado == RES_AGUA:
            self.casillas[fila][col] = AGUA
        elif resultado == RES_TOCADO:
            self.casillas[fila][col] = TOCADO
        elif resultado == RES_HUNDIDO:
            self.casillas[fila][col] = HUNDIDO

        return [(fila, col)]

    def a_dict(self):
        """Serializa el tablero de ataques para guardado JSON."""
        return {
            "tamano": self.tamano,
            "flota": {str(k): v for k, v in self.flota.items()},
            "barcos_pueden_tocarse": self.barcos_pueden_tocarse,
            "casillas": copy.deepcopy(self.casillas),
            "hundidos": list(self.hundidos),
        }

    @classmethod
    def desde_dict(cls, datos):
        """Reconstruye el tablero de ataques desde un diccionario."""
        t = cls(
            datos["tamano"],
            {int(k): v for k, v in datos["flota"].items()},
            datos.get("barcos_pueden_tocarse", True),
        )
        t.casillas = copy.deepcopy(datos["casillas"])
        return t
