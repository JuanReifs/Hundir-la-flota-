"""
constantes.py
-------------
Contrato global del proyecto: define todas las constantes y configuraciones
compartidas entre los módulos de juego, flota, ataques, pistas e interfaz.

Aquí se centraliza todo lo que no debe cambiar durante la ejecución:
tamaños de tablero, composición de la flota, estados de casilla, etc.
Así todos los archivos hablan el mismo idioma sin duplicar valores.

DAM2 - Acceso a Datos - CES Juan Pablo II.
"""

# Tamaño del tablero (10x10 según las especificaciones del proyecto)
TAMANO = 10

# Configuración oficial de la flota:
# 1 barco de 4 casillas (4)
# 2 barcos de 3 casillas (3)
# 3 barcos de 2 casillas (2)
# 4 barcos de 1 casilla (1)
CONFIGURACION_FLOTA = {4: 1, 3: 2, 2: 3, 1: 4}

# Estados numéricos de las casillas en el tablero de ataques
DESCONOCIDO = 0
AGUA = 1
TOCADO = 2
HUNDIDO = 3

# Cadenas de texto para los resultados de los disparos
RES_AGUA = "agua"
RES_TOCADO = "tocado"
RES_HUNDIDO = "hundido"
RESULTADOS_VALIDOS = (RES_AGUA, RES_TOCADO, RES_HUNDIDO)

# Identificadores de turno
TURNO_YO = "yo"
TURNO_RIVAL = "rival"

# Estados de la partida
ESTADO_EN_CURSO = "en_curso"
ESTADO_VICTORIA = "victoria"
ESTADO_DERROTA = "derrota"

# Archivo de guardado por defecto (para el módulo de Acceso a Datos)
ARCHIVO_GUARDADO = "partida.json"

# Letras para nombrar columnas si se desea formato A-J
LETRAS = "ABCDEFGHIJ"


def coord_a_texto(fila: int, col: int) -> str:
    """Convierte coordenadas numéricas (2, 1) a formato texto 'B3'.
    La letra es la columna (A-J) y el número es la fila (1-10)."""
    if 0 <= col < len(LETRAS):
        return f"{LETRAS[col]}{fila + 1}"
    return f"({fila}, {col})"


def texto_a_coord(texto: str, tamano: int = TAMANO) -> tuple[int, int]:
    """Convierte texto como 'B3' (col B, fila 3) o '3, 4' a coordenadas (fila, columna) [0..9]."""
    texto = texto.strip().upper()
    if not texto:
        raise ValueError("Coordenada vacía")

    # Formato letra + número (ej. B3 -> col=1, fila=2)
    if texto[0] in LETRAS[:tamano] and texto[1:].isdigit():
        col = LETRAS.index(texto[0])
        fila = int(texto[1:]) - 1
        if 0 <= fila < tamano:
            return fila, col
        raise ValueError(f"Coordenada fuera del tablero: '{texto}'")

    # Formato fila columna con coma o espacio (ej. '3,4' o '3 4' con índices 0-9)
    partes = texto.replace(",", " ").split()
    if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
        fila, col = int(partes[0]), int(partes[1])
        if 0 <= fila < tamano and 0 <= col < tamano:
            return fila, col

    raise ValueError(f"Coordenada no válida: '{texto}'")
