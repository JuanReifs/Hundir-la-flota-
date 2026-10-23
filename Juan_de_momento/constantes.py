"""Contrato de datos compartido por los tres integrantes.

Se acuerda el primer día y casi no se toca después.
"""

TAMANO = 10

# Flota por defecto: {tamaño del barco: cantidad}
FLOTA = {4: 1, 3: 2, 2: 3, 1: 4}

# Estados de una casilla del tablero de ataques
DESCONOCIDO, AGUA, TOCADO, HUNDIDO = 0, 1, 2, 3

# Resultados de un disparo
RES_AGUA, RES_TOCADO, RES_HUNDIDO = "agua", "tocado", "hundido"
RESULTADOS_VALIDOS = (RES_AGUA, RES_TOCADO, RES_HUNDIDO)

LETRAS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def coord_a_texto(fila: int, col: int) -> str:
    """(2, 1) -> 'B3'. La letra es la columna y el número la fila (desde 1)."""
    return f"{LETRAS[col]}{fila + 1}"


def texto_a_coord(texto: str, tamano: int = TAMANO) -> tuple[int, int]:
    """'B3' -> (2, 1). Lanza ValueError si el texto no es una coordenada válida."""
    texto = texto.strip().upper()
    if len(texto) < 2 or texto[0] not in LETRAS[:tamano] or not texto[1:].isdigit():
        raise ValueError(f"Coordenada no válida: '{texto}'")
    col = LETRAS.index(texto[0])
    fila = int(texto[1:]) - 1
    if not 0 <= fila < tamano:
        raise ValueError(f"Coordenada fuera del tablero: '{texto}'")
    return fila, col
