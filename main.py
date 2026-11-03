import sys
import subprocess
import os
import time

# --------------------------------------------------
# INSTALAR DEPENDENCIAS SI ES NECESARIO
# --------------------------------------------------

try:
    import pygame
    import cv2
    print("Las dependencias ya están instaladas.")

except ImportError:
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "pygame", "opencv-python"
    ])

    import pygame
    import cv2


# --------------------------------------------------
# INICIALIZAR PYGAME
# --------------------------------------------------

pygame.init()

try:
    pygame.mixer.init()
except pygame.error:
    print("No se ha podido inicializar el audio.")

ancho = 1000
alto = 650

pantalla = pygame.display.set_mode((ancho, alto))
pygame.display.set_caption("BATTLESHIP")

reloj = pygame.time.Clock()


# --------------------------------------------------
# COLORES
# --------------------------------------------------

blanco = (255, 255, 255)
negro = (0, 0, 0)
negro_grisaceo = (15, 15, 15)
verde_oscuro = (20, 83, 45)
verde_claro = (34, 120, 60)
rojo = (180, 30, 30)
gris = (100, 100, 100)
gris_claro = (190, 190, 190)


# --------------------------------------------------
# RUTAS DE LOS RECURSOS
# --------------------------------------------------

RUTA_IMAGENES = "Recursos/Imagenes"
RUTA_VIDEOS = "Recursos/Videos"
RUTA_SONIDOS = "Recursos/Sonidos"


# --------------------------------------------------
# FUENTES
# --------------------------------------------------

fuente_titulo = pygame.font.SysFont("arial", 52, bold=True)
fuente_grande = pygame.font.SysFont("arial", 28, bold=True)
fuente_normal = pygame.font.SysFont("arial", 22)
fuente_pequena = pygame.font.SysFont("arial", 17)


# --------------------------------------------------
# CARGAR IMÁGENES DE LOS BARCOS
# --------------------------------------------------

def cargar_imagen(ruta):
    try:
        imagen = pygame.image.load(ruta).convert_alpha()
        return imagen

    except (pygame.error, FileNotFoundError):
        print(f"No se ha podido cargar la imagen: {ruta}")
        return None


imagen_barcos = {
    1: cargar_imagen(
        os.path.join(RUTA_IMAGENES, "barco-1.png")
    ),

    2: cargar_imagen(
        os.path.join(RUTA_IMAGENES, "barco-2.png")
    ),

    3: cargar_imagen(
        os.path.join(RUTA_IMAGENES, "barco-3.png")
    ),

    4: cargar_imagen(
        os.path.join(RUTA_IMAGENES, "barco-4.png")
    )
}


# Imagen del fondo de la pantalla de juego
imagen_fondo_juego = cargar_imagen(
    os.path.join(RUTA_IMAGENES, "juego.png")
)

if imagen_fondo_juego is not None:
    imagen_fondo_juego = pygame.transform.scale(
        imagen_fondo_juego,
        (ancho, alto)
    )

imagen_fondo_colocacion = cargar_imagen(
    os.path.join(RUTA_IMAGENES, "posicionar_barcos.png")
)

if imagen_fondo_colocacion is not None:
    imagen_fondo_colocacion = pygame.transform.scale(
        imagen_fondo_colocacion,
        (ancho, alto)
    )


# --------------------------------------------------
# AUDIO
# --------------------------------------------------

try:
    sonido_barco = pygame.mixer.Sound(
        os.path.join(RUTA_SONIDOS, "barco.mp3")
    )
    sonido_barco.set_volume(0.7)

except pygame.error as error:
    print("No se ha podido cargar el sonido del barco:", error)
    sonido_barco = None

try:
    pygame.mixer.music.load(
        os.path.join(RUTA_SONIDOS, "inicio.mp3")
    )
    pygame.mixer.music.set_volume(0.35)

    sonido_boton = pygame.mixer.Sound(
        os.path.join(RUTA_SONIDOS, "Boton_inicio.mp3")
    )
    sonido_boton.set_volume(0.7)

except pygame.error as error:
    print("No se han podido cargar algunos sonidos:", error)
    sonido_boton = None


# --------------------------------------------------
# FUNCIONES GENERALES
# --------------------------------------------------

def dibujar_texto(texto, fuente, color, x, y, centrar=False):
    superficie = fuente.render(str(texto), True, color)

    if centrar:
        rectangulo = superficie.get_rect(center=(x, y))
    else:
        rectangulo = superficie.get_rect(topleft=(x, y))

    pantalla.blit(superficie, rectangulo)


def reproducir_sonido_boton():
    if sonido_boton is not None:
        sonido_boton.play()


def dibujar_boton(rectangulo, texto, activo=True):
    raton = pygame.mouse.get_pos()

    if not activo:
        color = gris
    elif rectangulo.collidepoint(raton):
        color = verde_claro
    else:
        color = verde_oscuro

    pygame.draw.rect(
        pantalla,
        color,
        rectangulo,
        border_radius=10
    )

    pygame.draw.rect(
        pantalla,
        blanco,
        rectangulo,
        width=2,
        border_radius=10
    )

    dibujar_texto(
        texto,
        fuente_normal,
        blanco,
        rectangulo.centerx,
        rectangulo.centery,
        centrar=True
    )


def dibujar_video(captura):
    correcto, fotograma = captura.read()

    if not correcto:
        captura.set(cv2.CAP_PROP_POS_FRAMES, 0)
        correcto, fotograma = captura.read()

    if correcto:
        fotograma = cv2.cvtColor(
            fotograma,
            cv2.COLOR_BGR2RGB
        )

        fotograma = cv2.resize(
            fotograma,
            (ancho, alto)
        )

        superficie = pygame.surfarray.make_surface(
            fotograma.swapaxes(0, 1)
        )

        pantalla.blit(superficie, (0, 0))


def abrir_video(ruta):
    captura = cv2.VideoCapture(ruta)

    if not captura.isOpened():
        print(f"No se ha podido abrir el vídeo: {ruta}")
        captura.release()
        return None

    return captura


def reproducir_transicion(ruta, duracion):
    captura = abrir_video(ruta)

    if captura is None:
        return

    inicio = time.time()

    while time.time() - inicio < duracion:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                captura.release()
                pygame.quit()
                sys.exit()

        dibujar_video(captura)
        pygame.display.flip()
        reloj.tick(30)

    captura.release()


# --------------------------------------------------
# PANTALLA DE MENÚ
# --------------------------------------------------

boton_iniciar = pygame.Rect(350, 370, 300, 65)
boton_salir = pygame.Rect(350, 460, 300, 65)


def pantalla_menu():
    captura = abrir_video(
        os.path.join(RUTA_VIDEOS, "Inicio.mp4")
    )

    if captura is None:
        fondo = pygame.Surface((ancho, alto))
        fondo.fill(negro_grisaceo)
    else:
        fondo = None

    try:
        pygame.mixer.music.play(-1)
    except pygame.error:
        pass

    while True:
        if captura is not None:
            dibujar_video(captura)
        else:
            pantalla.blit(fondo, (0, 0))
        dibujar_boton(boton_iniciar, "Iniciar juego")
        dibujar_boton(boton_salir, "Salir")

        pygame.display.flip()

        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:
                if captura is not None:
                    captura.release()

                pygame.quit()
                sys.exit()

            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:

                    if boton_iniciar.collidepoint(evento.pos):
                        reproducir_sonido_boton()

                        if captura is not None:
                            captura.release()

                        pygame.mixer.music.stop()
                        pantalla_configuracion()
                        return

                    elif boton_salir.collidepoint(evento.pos):
                        pygame.quit()
                        sys.exit()

        reloj.tick(60)


# --------------------------------------------------
# CONFIGURACIÓN DEL ENEMIGO
# --------------------------------------------------

nombre_enemigo = ""
primer_atacante = "Tu"


def pantalla_configuracion():
    global nombre_enemigo, primer_atacante

    campo_nombre = pygame.Rect(300, 220, 400, 45)

    boton_tu = pygame.Rect(300, 330, 180, 50)
    boton_enemigo = pygame.Rect(520, 330, 180, 50)

    boton_aceptar = pygame.Rect(350, 450, 300, 60)

    nombre_enemigo = ""
    primer_atacante = "Tu"

    activo_nombre = True
    mensaje_error = ""

    while True:
        pantalla.fill(negro_grisaceo)

        dibujar_texto(
            "CONFIGURACIÓN",
            fuente_titulo,
            blanco,
            ancho // 2,
            100,
            centrar=True
        )

        dibujar_texto(
            "Nombre del enemigo:",
            fuente_normal,
            blanco,
            campo_nombre.x,
            campo_nombre.y - 35
        )

        pygame.draw.rect(
            pantalla,
            blanco,
            campo_nombre,
            border_radius=5
        )

        pygame.draw.rect(
            pantalla,
            verde_claro if activo_nombre else gris,
            campo_nombre,
            width=2,
            border_radius=5
        )

        dibujar_texto(
            nombre_enemigo,
            fuente_normal,
            negro,
            campo_nombre.x + 10,
            campo_nombre.y + 8
        )

        dibujar_texto(
            "¿Quién ataca primero?",
            fuente_normal,
            blanco,
            ancho // 2,
            290,
            centrar=True
        )

        dibujar_boton(
            boton_tu,
            "Tú",
            activo=(primer_atacante == "Tu")
        )

        dibujar_boton(
            boton_enemigo,
            "Enemigo",
            activo=(primer_atacante == "Enemigo")
        )

        dibujar_boton(boton_aceptar, "Aceptar")

        if mensaje_error:
            dibujar_texto(
                mensaje_error,
                fuente_pequena,
                rojo,
                ancho // 2,
                535,
                centrar=True
            )

        pygame.display.flip()

        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:

                    activo_nombre = campo_nombre.collidepoint(
                        evento.pos
                    )

                    if boton_tu.collidepoint(evento.pos):
                        primer_atacante = "Tu"
                        reproducir_sonido_boton()

                    elif boton_enemigo.collidepoint(evento.pos):
                        primer_atacante = "Enemigo"
                        reproducir_sonido_boton()

                    elif boton_aceptar.collidepoint(evento.pos):
                        if nombre_enemigo.strip() == "":
                            mensaje_error = (
                                "Escribe el nombre del enemigo."
                            )
                        else:
                            reproducir_sonido_boton()

                            # Transición: vídeo inicial durante 3 s.
                            reproducir_transicion(
                                os.path.join(
                                    RUTA_VIDEOS, "Inicio.mp4"
                                ),
                                3
                            )

                            # Después, vídeo de carga durante 6 s.
                            reproducir_transicion(
                                os.path.join(
                                    RUTA_VIDEOS, "cargando.mp4"
                                ),
                                6
                            )

                            pantalla_juego()
                            return

            if evento.type == pygame.KEYDOWN and activo_nombre:

                if evento.key == pygame.K_RETURN:
                    activo_nombre = False

                elif evento.key == pygame.K_BACKSPACE:
                    nombre_enemigo = nombre_enemigo[:-1]

                elif len(nombre_enemigo) < 20:
                    if evento.unicode.isprintable():
                        nombre_enemigo += evento.unicode

        reloj.tick(60)


# --------------------------------------------------
# TABLERO Y BARCOS
# --------------------------------------------------

FILAS = 10
COLUMNAS = 10

TAM_CELDA = 50

TABLERO_X = 450
TABLERO_Y = 75

# Cada barco colocado se guarda en esta lista.
barcos_colocados = []

# Casillas ocupadas: se guardan como parejas (fila, columna).
casillas_ocupadas = set()

# Longitud seleccionada por el usuario.
longitud_seleccionada = 2

# Dirección a la que apunta el morro.
orientacion_seleccionada = "N"

# Campos de fila y columna.
texto_fila = "1"
texto_columna = "1"

campo_fila = pygame.Rect(35, 385, 75, 38)
campo_columna = pygame.Rect(145, 385, 75, 38)

campo_activo = "fila"


# --------------------------------------------------
# BOTONES DEL TABLERO
# --------------------------------------------------

# Selección de longitud: un poco más abajo.
boton_longitud_1 = pygame.Rect(30, 200, 70, 42)
boton_longitud_2 = pygame.Rect(110, 200, 70, 42)
boton_longitud_3 = pygame.Rect(190, 200, 70, 42)
boton_longitud_4 = pygame.Rect(30, 255, 70, 42)

# Orientación del morro.
boton_norte = pygame.Rect(115, 255, 65, 42)
boton_sur = pygame.Rect(190, 255, 65, 42)
boton_este = pygame.Rect(115, 310, 65, 42)
boton_oeste = pygame.Rect(190, 310, 65, 42)

# Botones de acción, más arriba.
boton_colocar = pygame.Rect(30, 455, 230, 48)
boton_limpiar = pygame.Rect(30, 515, 230, 40)


# --------------------------------------------------
# COLOCACIÓN Y ORIENTACIÓN DE LOS BARCOS
# --------------------------------------------------

def obtener_casillas_barco(fila, columna, longitud, orientacion):
    """
    La fila y la columna indican la casilla donde está el morro.

    N: el morro apunta al norte.
       El resto del barco va hacia las filas inferiores.

    S: el morro apunta al sur.
       El resto del barco va hacia las filas superiores.

    E: el morro apunta al este.
       El resto del barco va hacia las columnas anteriores.

    O: el morro apunta al oeste.
       El resto del barco va hacia las columnas siguientes.

    Las filas y columnas empiezan en 1.
    """

    casillas = []

    for i in range(longitud):

        if orientacion == "N":
            fila_actual = fila + i
            columna_actual = columna

        elif orientacion == "S":
            fila_actual = fila - i
            columna_actual = columna

        elif orientacion == "E":
            fila_actual = fila
            columna_actual = columna - i

        elif orientacion == "O":
            fila_actual = fila
            columna_actual = columna + i

        else:
            return []

        if not (
            1 <= fila_actual <= FILAS
            and 1 <= columna_actual <= COLUMNAS
        ):
            return []

        casillas.append((fila_actual, columna_actual))

    return casillas


def colocar_barco():
    global mensaje_tablero

    # Comprobar si ya existe un barco de este tamaño.
    for barco in barcos_colocados:
        if barco["longitud"] == longitud_seleccionada:
            mensaje_tablero = (
                f"Ya has colocado el barco de tamaño {longitud_seleccionada}."
            )
            return False

    try:
        fila = int(texto_fila)
        columna = int(texto_columna)

    except ValueError:
        mensaje_tablero = "Introduce una fila y columna válidas."
        return False

    if not (1 <= fila <= FILAS):
        mensaje_tablero = "La fila debe estar entre 1 y 10."
        return False

    if not (1 <= columna <= COLUMNAS):
        mensaje_tablero = "La columna debe estar entre 1 y 10."
        return False

    # El barco de una casilla no necesita orientación.
    if longitud_seleccionada == 1:
        orientacion = None
        casillas = [(fila, columna)]

    else:
        orientacion = orientacion_seleccionada

        casillas = obtener_casillas_barco(
            fila,
            columna,
            longitud_seleccionada,
            orientacion
        )

    if not casillas:
        mensaje_tablero = (
            "El barco se sale del tablero con esa orientación."
        )
        return False

    # Comprobar que no ocupa casillas de otros barcos.
    for casilla in casillas:
        if casilla in casillas_ocupadas:
            mensaje_tablero = (
                "No puedes colocar barcos encima de otros."
            )
            return False

    # Guardar el barco.
    barco = {
        "fila": fila,
        "columna": columna,
        "longitud": longitud_seleccionada,
        "orientacion": orientacion,
        "casillas": casillas
    }

    barcos_colocados.append(barco)

    for casilla in casillas:
        casillas_ocupadas.add(casilla)

    mensaje_tablero = (
        f"Barco de tamaño {longitud_seleccionada} colocado correctamente."
    )

    print("Barcos colocados:")

    for barco_guardado in barcos_colocados:
        print(barco_guardado)

    return True

def todos_los_barcos_colocados():

    # Necesitamos exactamente estos cuatro tamaños.
    tamanos_necesarios = {1, 2, 3, 4}

    # Obtener los tamaños de los barcos colocados.
    tamanos_colocados = {
        barco["longitud"] for barco in barcos_colocados
    }

    # Solo empieza cuando están los cuatro tamaños.
    return tamanos_colocados == tamanos_necesarios

def transicion_a_partida():

    # Reproducir el sonido del barco
    if sonido_barco is not None:
        sonido_barco.play()

    # Esperar 2 segundos sin congelar la ventana
    reloj = pygame.time.Clock()
    tiempo_inicio = pygame.time.get_ticks()

    while pygame.time.get_ticks() - tiempo_inicio < 2000:

        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

        reloj.tick(60)

    # Pasar directamente a la pantalla de partida
    pantalla_partida()

def pantalla_partida():

    reloj = pygame.time.Clock()

    # Botones de ejemplo
    boton_atacar = pygame.Rect(700, 400, 220, 60)
    boton_salir_partida = pygame.Rect(700, 490, 220, 60)

    ejecutando = True

    while ejecutando:

        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:
                ejecutando = False

            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:

                    if boton_atacar.collidepoint(evento.pos):
                        print("Botón Atacar pulsado")

                    elif boton_salir_partida.collidepoint(evento.pos):
                        ejecutando = False

        # Dibujar el fondo de la partida
        if imagen_fondo_juego is not None:
            pantalla.blit(
                imagen_fondo_juego,
                (0, 0)
            )
        else:
            pantalla.fill(negro)

        # Dibujar los botones
        dibujar_boton(
            boton_atacar,
            "Atacar"
        )

        dibujar_boton(
            boton_salir_partida,
            "Salir"
        )

        pygame.display.flip()
        reloj.tick(60)

def limpiar_barcos():
    global mensaje_tablero

    barcos_colocados.clear()
    casillas_ocupadas.clear()

    mensaje_tablero = "Se han eliminado todos los barcos."


# --------------------------------------------------
# DIBUJAR TABLERO
# --------------------------------------------------

def dibujar_tablero():
    # Números de las columnas.
    # NÚMEROS DE LAS COLUMNAS DEBAJO DEL TABLERO
    for columna in range(1, COLUMNAS + 1):
        x = TABLERO_X + (columna - 1) * TAM_CELDA

        dibujar_texto(
            str(columna),
            fuente_pequena,
            blanco,
            x + TAM_CELDA // 2,
            TABLERO_Y + FILAS * TAM_CELDA + 15,
            centrar=True
        )

    # Números de las filas.
    for fila in range(1, FILAS + 1):
        y = TABLERO_Y + (fila - 1) * TAM_CELDA

        dibujar_texto(
            str(fila),
            fuente_pequena,
            blanco,
            TABLERO_X - 22,
            y + TAM_CELDA // 2,
            centrar=True
        )

    # Dibujar las casillas vacías.
    for fila in range(1, FILAS + 1):
        for columna in range(1, COLUMNAS + 1):

            x = TABLERO_X + (columna - 1) * TAM_CELDA
            y = TABLERO_Y + (fila - 1) * TAM_CELDA

            rectangulo = pygame.Rect(
                x,
                y,
                TAM_CELDA,
                TAM_CELDA
            )

            pygame.draw.rect(
                pantalla,
                (20, 65, 85),
                rectangulo
            )

            pygame.draw.rect(
                pantalla,
                (110, 160, 175),
                rectangulo,
                width=1
            )

    # Dibujar las imágenes de los barcos ya colocados.
    for barco in barcos_colocados:
        dibujar_imagen_barco(barco)

    # Dibujar una previsualización del barco que se va a colocar.
    dibujar_previsualizacion()


# --------------------------------------------------
# DIBUJAR IMAGEN DE UN BARCO
# --------------------------------------------------

def dibujar_imagen_barco(barco):
    longitud = barco["longitud"]
    orientacion = barco["orientacion"]

    imagen = imagen_barcos.get(longitud)

    # Si falta una imagen, mostramos un aviso en la terminal.
    # No dibujamos cuadrados como sustituto.
    if imagen is None:
        return

    # La imagen original debe tener el morro hacia la IZQUIERDA.
    # A partir de esa orientación, la giramos según corresponda.
    if longitud > 1:

        if orientacion == "O":
            imagen_girada = imagen

        elif orientacion == "E":
            imagen_girada = pygame.transform.rotate(
                imagen,
                180
            )

        elif orientacion == "N":
            imagen_girada = pygame.transform.rotate(
                imagen,
                -90
            )

        elif orientacion == "S":
            imagen_girada = pygame.transform.rotate(
                imagen,
                90
            )

        else:
            imagen_girada = imagen

    else:
        imagen_girada = imagen

    casillas = barco["casillas"]

    filas_barco = [casilla[0] for casilla in casillas]
    columnas_barco = [casilla[1] for casilla in casillas]

    fila_min = min(filas_barco)
    fila_max = max(filas_barco)

    columna_min = min(columnas_barco)
    columna_max = max(columnas_barco)

    x = TABLERO_X + (columna_min - 1) * TAM_CELDA
    y = TABLERO_Y + (fila_min - 1) * TAM_CELDA

    ancho_barco = (
        columna_max - columna_min + 1
    ) * TAM_CELDA

    alto_barco = (
        fila_max - fila_min + 1
    ) * TAM_CELDA

    imagen_girada = pygame.transform.smoothscale(
        imagen_girada,
        (ancho_barco, alto_barco)
    )

    pantalla.blit(imagen_girada, (x, y))


# --------------------------------------------------
# PREVISUALIZAR EL BARCO ANTES DE COLOCARLO
# --------------------------------------------------

def dibujar_previsualizacion():
    try:
        fila = int(texto_fila)
        columna = int(texto_columna)

    except ValueError:
        return

    if not (
        1 <= fila <= FILAS
        and 1 <= columna <= COLUMNAS
    ):
        return

    if longitud_seleccionada == 1:
        casillas = [(fila, columna)]
        orientacion = None

    else:
        orientacion = orientacion_seleccionada

        casillas = obtener_casillas_barco(
            fila,
            columna,
            longitud_seleccionada,
            orientacion
        )

    if not casillas:
        return

    # No mostrar la previsualización si invade un barco colocado.
    if any(casilla in casillas_ocupadas for casilla in casillas):
        return

    barco_temporal = {
        "fila": fila,
        "columna": columna,
        "longitud": longitud_seleccionada,
        "orientacion": orientacion,
        "casillas": casillas
    }

    imagen = imagen_barcos.get(longitud_seleccionada)

    if imagen is None:
        return

    # Transparencia para distinguir la previsualización.
    imagen_temporal = imagen.copy()
    imagen_temporal.set_alpha(140)

    if longitud_seleccionada > 1:

        if orientacion == "O":
            imagen_girada = imagen_temporal

        elif orientacion == "E":
            imagen_girada = pygame.transform.rotate(
                imagen_temporal,
                180
            )

        elif orientacion == "N":
            imagen_girada = pygame.transform.rotate(
                imagen_temporal,
                -90
            )

        else:  # Sur
            imagen_girada = pygame.transform.rotate(
                imagen_temporal,
                90
            )

    else:
        imagen_girada = imagen_temporal

    filas_barco = [casilla[0] for casilla in casillas]
    columnas_barco = [casilla[1] for casilla in casillas]

    fila_min = min(filas_barco)
    fila_max = max(filas_barco)

    columna_min = min(columnas_barco)
    columna_max = max(columnas_barco)

    x = TABLERO_X + (columna_min - 1) * TAM_CELDA
    y = TABLERO_Y + (fila_min - 1) * TAM_CELDA

    ancho_barco = (
        columna_max - columna_min + 1
    ) * TAM_CELDA

    alto_barco = (
        fila_max - fila_min + 1
    ) * TAM_CELDA

    imagen_girada = pygame.transform.smoothscale(
        imagen_girada,
        (ancho_barco, alto_barco)
    )

    pantalla.blit(imagen_girada, (x, y))


# --------------------------------------------------
# DIBUJAR LOS CONTROLES DE COLOCACIÓN
# --------------------------------------------------

# --------------------------------------------------
# DIBUJAR LOS CONTROLES DE COLOCACIÓN
# --------------------------------------------------

def dibujar_controles():

    # LONGITUD DEL BARCO
    dibujar_texto(
        "Longitud:",
        fuente_normal,
        blanco,
        30,
        165
    )

    botones_longitud = [
        (boton_longitud_1, "1", 1),
        (boton_longitud_2, "2", 2),
        (boton_longitud_3, "3", 3),
        (boton_longitud_4, "4", 4)
    ]

    for rectangulo, texto, longitud in botones_longitud:
        dibujar_boton(
            rectangulo,
            texto,
            activo=(longitud_seleccionada == longitud)
        )

    # ORIENTACIÓN DEL MORRO
    dibujar_texto(
        "Orientación del morro:",
        fuente_pequena,
        blanco,
        30,
        225
    )

    orientaciones = [
        (boton_norte, "N", "N"),
        (boton_sur, "S", "S"),
        (boton_este, "E", "E"),
        (boton_oeste, "O", "O")
    ]

    orientacion_activa = longitud_seleccionada > 1

    for rectangulo, texto, orientacion in orientaciones:
        dibujar_boton(
            rectangulo,
            texto,
            activo=(
                orientacion_activa
                and orientacion_seleccionada == orientacion
            )
        )

    # FILA Y COLUMNA, JUSTO DEBAJO DE LA ORIENTACIÓN
    dibujar_texto(
        "Fila (1-10):",
        fuente_pequena,
        blanco,
        campo_fila.x,
        campo_fila.y - 25
    )

    dibujar_texto(
        "Columna (1-10):",
        fuente_pequena,
        blanco,
        campo_columna.x - 5,
        campo_columna.y - 25
    )

    # Campo de fila
    pygame.draw.rect(
        pantalla,
        blanco,
        campo_fila,
        border_radius=5
    )

    pygame.draw.rect(
        pantalla,
        verde_claro if campo_activo == "fila" else gris,
        campo_fila,
        width=2,
        border_radius=5
    )

    # Campo de columna
    pygame.draw.rect(
        pantalla,
        blanco,
        campo_columna,
        border_radius=5
    )

    pygame.draw.rect(
        pantalla,
        verde_claro if campo_activo == "columna" else gris,
        campo_columna,
        width=2,
        border_radius=5
    )

    # Mostrar los números introducidos
    dibujar_texto(
        texto_fila,
        fuente_normal,
        negro,
        campo_fila.x + 10,
        campo_fila.y + 5
    )

    dibujar_texto(
        texto_columna,
        fuente_normal,
        negro,
        campo_columna.x + 10,
        campo_columna.y + 5
    )

    # BOTONES DE ACCIÓN
    dibujar_boton(
        boton_colocar,
        "Colocar barco"
    )

    dibujar_boton(
        boton_limpiar,
        "Eliminar todos"
    )

    # MENSAJE DE ESTADO
    if mensaje_tablero:
        dibujar_texto(
            mensaje_tablero,
            fuente_pequena,
            blanco,
            25,
            570
        )


# --------------------------------------------------
# PANTALLA DE JUEGO
# --------------------------------------------------

def pantalla_juego():
    global longitud_seleccionada
    global orientacion_seleccionada
    global texto_fila, texto_columna
    global campo_activo, mensaje_tablero

    # Empezar con el tablero vacío.
    barcos_colocados.clear()
    casillas_ocupadas.clear()

    longitud_seleccionada = 2
    orientacion_seleccionada = "N"

    texto_fila = "1"
    texto_columna = "1"

    campo_activo = "fila"
    mensaje_tablero = ""

    while True:

        # Mostrar el fondo original sin oscurecerlo.
        if imagen_fondo_colocacion is not None:
            pantalla.blit(imagen_fondo_colocacion, (0, 0))
        else:
            pantalla.fill(negro)

        dibujar_controles()
        dibujar_tablero()

        dibujar_texto(
            f"Enemigo: {nombre_enemigo}",
            fuente_pequena,
            blanco,
            740,
            20
        )

        dibujar_texto(
            f"Primer atacante: {primer_atacante}",
            fuente_pequena,
            blanco,
            740,
            45
        )

        pygame.display.flip()

        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # --------------------------------------
            # CLICS DEL RATÓN
            # --------------------------------------

            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:

                    if campo_fila.collidepoint(evento.pos):
                        campo_activo = "fila"

                    elif campo_columna.collidepoint(evento.pos):
                        campo_activo = "columna"

                    # Seleccionar longitud 1.
                    elif boton_longitud_1.collidepoint(evento.pos):
                        longitud_seleccionada = 1
                        mensaje_tablero = (
                            "Barco de 1 casilla: orientación desactivada."
                        )

                    # Seleccionar longitud 2.
                    elif boton_longitud_2.collidepoint(evento.pos):
                        longitud_seleccionada = 2
                        mensaje_tablero = ""

                    # Seleccionar longitud 3.
                    elif boton_longitud_3.collidepoint(evento.pos):
                        longitud_seleccionada = 3
                        mensaje_tablero = ""

                    # Seleccionar longitud 4.
                    elif boton_longitud_4.collidepoint(evento.pos):
                        longitud_seleccionada = 4
                        mensaje_tablero = ""

                    # Seleccionar orientación.
                    # Solo funciona para barcos de longitud mayor que 1.
                    elif longitud_seleccionada > 1:

                        if boton_norte.collidepoint(evento.pos):
                            orientacion_seleccionada = "N"

                        elif boton_sur.collidepoint(evento.pos):
                            orientacion_seleccionada = "S"

                        elif boton_este.collidepoint(evento.pos):
                            orientacion_seleccionada = "E"

                        elif boton_oeste.collidepoint(evento.pos):
                            orientacion_seleccionada = "O"

                    # --------------------------------------
                    # COLOCAR BARCO Y COMPROBAR SI ESTÁN TODOS
                    # --------------------------------------

                    if boton_colocar.collidepoint(evento.pos):

                        barco_colocado = colocar_barco()

                        # Solo comprobamos el inicio si el barco se ha colocado correctamente.
                        if barco_colocado and todos_los_barcos_colocados():
                            transicion_a_partida()
                            return

                    # Limpiar los barcos colocados.
                    elif boton_limpiar.collidepoint(evento.pos):
                        limpiar_barcos()

                    reproducir_sonido_boton()

            # --------------------------------------
            # ESCRIBIR FILA Y COLUMNA
            # --------------------------------------

            if evento.type == pygame.KEYDOWN:

                if campo_activo == "fila":

                    if evento.key == pygame.K_BACKSPACE:
                        texto_fila = texto_fila[:-1]

                    elif evento.unicode.isdigit():
                        if len(texto_fila) < 2:
                            texto_fila += evento.unicode

                    elif evento.key == pygame.K_TAB:
                        campo_activo = "columna"

                elif campo_activo == "columna":

                    if evento.key == pygame.K_BACKSPACE:
                        texto_columna = texto_columna[:-1]

                    elif evento.unicode.isdigit():
                        if len(texto_columna) < 2:
                            texto_columna += evento.unicode

                    elif evento.key == pygame.K_TAB:
                        campo_activo = "fila"

        reloj.tick(60)

# --------------------------------------------------
# INICIAR EL PROGRAMA
# --------------------------------------------------

if __name__ == "__main__":
    pantalla_menu()