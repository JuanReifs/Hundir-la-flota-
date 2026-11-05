"""
flota.py
--------
Gestión del tablero propio del jugador y colocación aleatoria de la flota.

Este módulo se encarga de:
- Crear la matriz 10x10 (0 = agua, 1/2/3/4 = barcos según su tamaño).
- Colocar aleatoriamente los 10 barcos sin diagonales ni superposiciones.
- Procesar los ataques recibidos del rival y devolver agua/tocado/hundido.
- Serializar y deserializar el estado para guardado en JSON.

DAM2 - Acceso a Datos - CES Juan Pablo II.
"""

import json
import random
from constantes import TAMANO, CONFIGURACION_FLOTA, RES_AGUA, RES_TOCADO, RES_HUNDIDO


class Flota:
    """Clase que representa el tablero del jugador con sus barcos e impactos recibidos."""

    def __init__(self, tamano=TAMANO, configuracion=None):
        self.tamano = tamano
        if configuracion is None:
            # 1 de 4, 2 de 3, 3 de 2, 4 de 1
            configuracion = dict(CONFIGURACION_FLOTA)

        self.configuracion = configuracion
        self.barcos = []
        self.tablero = []
        # Diccionario para rastrear los disparos recibidos: (fila, col) -> "agua"|"tocado"|"hundido"
        self.disparos_recibidos = {}

        self.crear_tablero()
        self.colocar_flota()

    def crear_tablero(self):
        """Crea la matriz de 10x10 rellena de 0 (agua)."""
        self.tablero = [[0 for _ in range(self.tamano)] for _ in range(self.tamano)]

    def posicion_valida(self, coordenadas):
        """
        Comprueba que las coordenadas del barco:
        1. Estén dentro de los límites del tablero.
        2. No se superpongan ni coincidan con otro barco ya colocado.
        3. No se toquen en diagonal (para evitar ambigüedades en el radar).
        """
        for fila, columna in coordenadas:
            # Límites del tablero (0 a 9)
            if fila < 0 or fila >= self.tamano or columna < 0 or columna >= self.tamano:
                return False

            # Comprobar colisión con barcos existentes
            for barco in self.barcos:
                for otra_fila, otra_columna in barco["coordenadas"]:
                    # No solapar
                    if fila == otra_fila and columna == otra_columna:
                        return False
                    # No coincidir en diagonales contiguas
                    if abs(fila - otra_fila) == 1 and abs(columna - otra_columna) == 1:
                        return False

        return True

    def generar_posiciones(self, longitud):
        """
        Genera todas las orientaciones válidas (horizontal o vertical)
        para un barco de longitud dada dentro del tablero de 10x10.
        """
        posiciones = []

        for fila in range(self.tamano):
            for columna in range(self.tamano):
                # Barco horizontal (hacia la derecha)
                if columna + longitud <= self.tamano:
                    horizontal = [[fila, columna + i] for i in range(longitud)]
                    posiciones.append(horizontal)

                # Barco vertical (hacia abajo, solo si longitud > 1 para no duplicar)
                if longitud > 1 and fila + longitud <= self.tamano:
                    vertical = [[fila + i, columna] for i in range(longitud)]
                    posiciones.append(vertical)

        # Barajamos aleatoriamente para que cada colocación sea única
        random.shuffle(posiciones)
        return posiciones

    def colocar_flota(self):
        """
        Coloca de forma aleatoria la flota respetando las restricciones:
        1 barco de 4, 2 de 3, 3 de 2 y 4 de 1.
        """
        self.barcos = []
        self.crear_tablero()

        # Ordenamos de mayor a menor para colocar primero los barcos más largos
        tamanos = sorted(self.configuracion.keys(), reverse=True)

        for longitud in tamanos:
            cantidad = self.configuracion[longitud]
            for _ in range(cantidad):
                posiciones = self.generar_posiciones(longitud)
                colocado = False

                for coords in posiciones:
                    if self.posicion_valida(coords):
                        barco = {
                            "tamano": longitud,
                            "coordenadas": coords,
                            "impactos": []
                        }
                        self.barcos.append(barco)

                        # En la matriz del tablero, representamos el barco con su número (4, 3, 2 o 1)
                        for f, c in coords:
                            self.tablero[f][c] = longitud

                        colocado = True
                        break

                if not colocado:
                    # En el improbable caso de bloqueo en tableros pequeños, reintentamos
                    return self.colocar_flota()

    def recibir_ataque(self, fila, columna):
        """
        Procesa un ataque recibido en las coordenadas (fila, columna):
        - Devuelve "agua" si no hay barco.
        - Devuelve "tocado" si impacta un barco pero aún le quedan casillas intactas.
        - Devuelve "hundido" si todas las casillas de ese barco han recibido impacto.
        Lanza ValueError si las coordenadas se salen del mapa o ya fueron atacadas.
        """
        if not (0 <= fila < self.tamano and 0 <= columna < self.tamano):
            raise ValueError(f"Coordenadas fuera del tablero: ({fila}, {columna})")

        pos = (fila, columna)
        if pos in self.disparos_recibidos:
            raise ValueError(f"La casilla ({fila}, {columna}) ya ha sido atacada anteriormente.")

        # Buscar si el ataque impacta a alguno de nuestros barcos
        for barco in self.barcos:
            if [fila, columna] in barco["coordenadas"]:
                barco["impactos"].append([fila, columna])
                # Comprobar si todas sus coordenadas han sido impactadas
                if len(barco["impactos"]) == barco["tamano"]:
                    # Marcar todas las casillas del barco como hundidas
                    for f, c in barco["coordenadas"]:
                        self.disparos_recibidos[(f, c)] = RES_HUNDIDO
                    return RES_HUNDIDO
                else:
                    self.disparos_recibidos[pos] = RES_TOCADO
                    return RES_TOCADO

        # Si no hay barco, es agua
        self.disparos_recibidos[pos] = RES_AGUA
        return RES_AGUA

    def todos_hundidos(self):
        """Devuelve True si todos los barcos de la flota han sido hundidos."""
        if not self.barcos:
            return False
        return all(len(b["impactos"]) >= b["tamano"] for b in self.barcos)

    def mostrar_tablero(self):
        """
        Imprime el tablero por consola en formato matriz de números (0, 1, 2, 3, 4)
        tal como se solicita en el PDF de especificaciones.
        """
        print("Tablero del jugador:")
        print("   " + " ".join(str(c) for c in range(self.tamano)))
        for f in range(self.tamano):
            fila_str = " ".join(str(self.tablero[f][c]) for c in range(self.tamano))
            print(f"{f:2} {fila_str}")

    def a_dict(self):
        """Serializa la flota y el tablero a un diccionario para JSON."""
        return {
            "tamano": self.tamano,
            "configuracion": {str(k): v for k, v in self.configuracion.items()},
            "barcos": self.barcos,
            "tablero": self.tablero,
            "disparos_recibidos": [
                {"fila": f, "columna": c, "resultado": res}
                for (f, c), res in self.disparos_recibidos.items()
            ]
        }

    @classmethod
    def desde_dict(cls, datos):
        """Reconstruye una instancia de Flota a partir de un diccionario."""
        flota = cls.__new__(cls)
        flota.tamano = datos["tamano"]
        flota.configuracion = {int(k): v for k, v in datos["configuracion"].items()}
        flota.barcos = datos["barcos"]
        flota.tablero = datos["tablero"]
        flota.disparos_recibidos = {
            (d["fila"], d["columna"]): d["resultado"]
            for d in datos.get("disparos_recibidos", [])
        }
        return flota

    def guardar_partida(self, archivo="tablero_propio.json"):
        """Guarda el estado del tablero propio en un archivo JSON."""
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(self.a_dict(), f, indent=4)

    @classmethod
    def cargar_partida(cls, archivo="tablero_propio.json"):
        """Carga el estado del tablero propio desde un archivo JSON."""
        with open(archivo, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return cls.desde_dict(datos)
