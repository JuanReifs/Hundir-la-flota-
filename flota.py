import random
import json

class Flota:

    def __init__(self, tamano=10, configuracion=None):
        self.tamano = tamano

        if configuracion is None:
            configuracion = {4: 1, 3: 2, 2: 3, 1: 4}

        self.configuracion = configuracion
        self.barcos = []
        self.tablero = []

        self.crear_tablero()
        self.colocar_flota()

    # Crear tablero vacío
    def crear_tablero(self):
        self.tablero = []

        for fila in range(self.tamano):
            nueva_fila = []

            for columna in range(self.tamano):
                nueva_fila.append("~")

            self.tablero.append(nueva_fila)

    # Comprobar si un barco puede colocarse
    def posicion_valida(self, coordenadas):
        for fila, columna in coordenadas:

            # Comprobar límites del tablero
            if fila < 0 or fila >= self.tamano:
                return False

            if columna < 0 or columna >= self.tamano:
                return False

            # Comprobar solapamientos y diagonales
            for barco in self.barcos:
                for otra_fila, otra_columna in barco["coordenadas"]:

                    if fila == otra_fila and columna == otra_columna:
                        return False

                    if (abs(fila - otra_fila) == 1
                            and abs(columna - otra_columna) == 1):
                        return False

        return True

    # Generar todas las posiciones posibles de un barco
    def generar_posiciones(self, longitud):
        posiciones = []

        for fila in range(self.tamano):
            for columna in range(self.tamano):

                # Barco horizontal
                horizontal = []

                for i in range(longitud):
                    horizontal.append([fila, columna + i])

                if columna + longitud <= self.tamano:
                    posiciones.append(horizontal)

                # Barco vertical
                vertical = []

                for i in range(longitud):
                    vertical.append([fila + i, columna])

                if fila + longitud <= self.tamano:
                    posiciones.append(vertical)

        random.shuffle(posiciones)
        return posiciones

    # Colocar todos los barcos aleatoriamente
    def colocar_flota(self):
        for longitud, cantidad in self.configuracion.items():

            for i in range(cantidad):
                posiciones = self.generar_posiciones(longitud)
                colocado = False

                for coordenadas in posiciones:
                    if self.posicion_valida(coordenadas):

                        barco = {
                            "tamano": longitud,
                            "coordenadas": coordenadas,
                            "impactos": []
                        }

                        self.barcos.append(barco)

                        for fila, columna in coordenadas:
                            self.tablero[fila][columna] = "B"

                        colocado = True
                        break

                if not colocado:
                    raise ValueError(
                        "No se ha podido colocar toda la flota"
                    )

    # Recibir un ataque
    def recibir_ataque(self, fila, columna):

        # Comprobar que las coordenadas son válidas
        if not (0 <= fila < self.tamano
                and 0 <= columna < self.tamano):
            raise ValueError("Coordenadas fuera del tablero")

        # Comprobar si ya se ha atacado esa casilla
        if self.tablero[fila][columna] in ("X", "O"):
            return "ya atacada"

        # Buscar si el ataque alcanza un barco
        for barco in self.barcos:

            if [fila, columna] in barco["coordenadas"]:

                barco["impactos"].append([fila, columna])
                hundido = all(
                    coordenada in barco["impactos"]
                    for coordenada in barco["coordenadas"]
                )

                self.tablero[fila][columna] = "X"

                if hundido:
                    if self.todos_hundidos():
                        return "derrota"
                    return "hundido"

                return "tocado"

        # Si no hay barco, es agua
        self.tablero[fila][columna] = "O"
        return "agua"

    # Comprobar si todos los barcos están hundidos
    def todos_hundidos(self):
        for barco in self.barcos:
            if len(barco["impactos"]) < barco["tamano"]:
                return False

        return True

    # Mostrar el tablero
    def mostrar_tablero(self):
        print("   ", end="")

        for columna in range(self.tamano):
            print(f"{columna:2}", end="")

        print()

        for fila in range(self.tamano):
            print(f"{fila:2} ", end="")

            for columna in range(self.tamano):
                print(f"{self.tablero[fila][columna]:2}", end="")

            print()

    # Guardar partida en JSON
    def guardar_partida(self, archivo="partida.json"):
        datos = {
            "tamano": self.tamano,
            "configuracion": self.configuracion,
            "barcos": self.barcos,
            "tablero": self.tablero
        }

        with open(archivo, "w", encoding="utf-8") as fichero:
            json.dump(datos, fichero, indent=4)

    # Cargar partida desde JSON
    @classmethod
    def cargar_partida(cls, archivo="partida.json"):
        with open(archivo, "r", encoding="utf-8") as fichero:
            datos = json.load(fichero)

        juego = cls.__new__(cls)
        juego.tamano = datos["tamano"]

        juego.configuracion = {
            int(longitud): cantidad
            for longitud, cantidad
            in datos["configuracion"].items()
        }

        juego.barcos = datos["barcos"]
        juego.tablero = datos["tablero"]

        return juego
