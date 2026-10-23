
import sys
import subprocess

# INSTALAR DEPENDENCIAS SI FALTAN
try:
    import pygame
    import cv2

    print("Ya tienes las dependencias instaladas")

except ImportError:
    print("Instalando las dependencias del juego...")

    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "pygame"
    ])

    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "opencv-python"
    ])

    import pygame
    import cv2


pygame.init()
pygame.mixer.init()

# CONFIGURACION DE LA VENTANA
ancho = 1000
alto = 650

pantalla = pygame.display.set_mode((ancho, alto))
pygame.display.set_caption("BATTLESHIP")

reloj = pygame.time.Clock()

# COLORES
blanco = (255, 255, 255)
negro = (0, 0, 0)
negro_grisaceo = (15, 15, 15)
verde_oscuro = (20, 83, 45)
verde_claro = (34, 120, 60)
rojo = (180, 30, 30)
gris = (120, 120, 120)

# FUENTES
fuente = pygame.font.SysFont("arial", 28, bold=True)
fuente_pequena = pygame.font.SysFont("arial", 20)
fuente_titulo = pygame.font.SysFont("arial", 38, bold=True)

# INFORMACION PERSONALIZABLE
informacion_partida = (
    "Prepara tu flota para la batalla.\n"
    "Introduce el nombre de tu rival y decide\n"
    "quien realizara el primer ataque."
)

# VIDEO INICIAL
video = cv2.VideoCapture("Recursos/Videos/Inicio.mp4")

if not video.isOpened():
    pygame.quit()
    raise FileNotFoundError(
        "No se ha podido abrir Recursos/Videos/Inicio.mp4"
    )

fps_video = video.get(cv2.CAP_PROP_FPS)

if fps_video <= 0 or fps_video > 120:
    fps_video = 30

# VIDEO DE CARGA
video_carga = cv2.VideoCapture("Recursos/Videos/cargando.mp4")

if not video_carga.isOpened():
    video.release()
    pygame.quit()
    raise FileNotFoundError(
        "No se ha podido abrir Recursos/Videos/cargando.mp4"
    )

fps_carga = video_carga.get(cv2.CAP_PROP_FPS)

if fps_carga <= 0 or fps_carga > 120:
    fps_carga = 30

# IMAGEN DEL JUEGO
fondo_juego = pygame.image.load(
    "Recursos/Imagenes/juego.png"
)

fondo_juego = pygame.transform.scale(
    fondo_juego, (ancho, alto)
)

# SONIDOS
pygame.mixer.music.load("Recursos/Sonidos/inicio.mp3")
pygame.mixer.music.set_volume(0.35)
pygame.mixer.music.play(-1)

sonido_boton = pygame.mixer.Sound(
    "Recursos/Sonidos/Boton_inicio.mp3"
)
sonido_boton.set_volume(0.7)

sonido_barco = pygame.mixer.Sound(
    "Recursos/Sonidos/Boton_inicio.mp3"
)
sonido_barco.set_volume(0.7)

# BOTONES DEL MENU PRINCIPAL
boton_iniciar = pygame.Rect(350, 400, 300, 65)
boton_salir = pygame.Rect(350, 490, 300, 65)

# ELEMENTOS DEL MENU DE CONFIGURACION
campo_nombre = pygame.Rect(300, 170, 400, 48)

boton_tu = pygame.Rect(300, 285, 180, 50)
boton_enemigo = pygame.Rect(520, 285, 180, 50)

boton_volver = pygame.Rect(200, 535, 250, 60)
boton_aceptar = pygame.Rect(550, 535, 250, 60)

# ESTADO DEL JUEGO
ejecutando = True
pantalla_actual = "menu"

# CONFIGURACION DE LA PARTIDA
nombre_enemigo = ""
primer_atacante = "Tu"
campo_activo = False

# TIEMPOS DE CARGA
tiempo_inicio_carga = 0
tiempo_inicio_video_carga = 0
video_cambiado = False

video_actual = video
fps_actual = fps_video

# BUCLE PRINCIPAL
while ejecutando:

    # EVENTOS
    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:
            ejecutando = False

        # ESCRIBIR EN EL CAMPO DEL NOMBRE
        if pantalla_actual == "configuracion":

            if evento.type == pygame.MOUSEBUTTONDOWN:

                if evento.button == 1:

                    campo_activo = campo_nombre.collidepoint(
                        evento.pos
                    )

                    # ELEGIR QUIEN ATACA PRIMERO
                    if boton_tu.collidepoint(evento.pos):
                        primer_atacante = "Tu"
                        sonido_boton.play()

                    elif boton_enemigo.collidepoint(evento.pos):
                        primer_atacante = "Enemigo"
                        sonido_boton.play()

                    # VOLVER AL MENU PRINCIPAL
                    elif boton_volver.collidepoint(evento.pos):
                        sonido_boton.play()
                        pantalla_actual = "menu"

                    # ACEPTAR LA CONFIGURACION
                    elif boton_aceptar.collidepoint(evento.pos):

                        if nombre_enemigo.strip() == "":
                            nombre_enemigo = "Enemigo"

                        sonido_boton.play()
                        pygame.mixer.music.stop()
                        sonido_barco.play()

                        tiempo_inicio_carga = (
                            pygame.time.get_ticks()
                        )

                        video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        video_actual = video
                        fps_actual = fps_video

                        video_cambiado = False
                        pantalla_actual = "carga"

            # ESCRIBIR Y BORRAR TEXTO
            if evento.type == pygame.KEYDOWN and campo_activo:

                if evento.key == pygame.K_BACKSPACE:
                    nombre_enemigo = nombre_enemigo[:-1]

                elif evento.key == pygame.K_RETURN:
                    campo_activo = False

                elif evento.unicode.isprintable():
                    if len(nombre_enemigo) < 25:
                        nombre_enemigo += evento.unicode

        # MENU PRINCIPAL
        elif pantalla_actual == "menu":

            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:

                    if boton_iniciar.collidepoint(evento.pos):
                        sonido_boton.play()
                        pantalla_actual = "configuracion"

                    elif boton_salir.collidepoint(evento.pos):
                        ejecutando = False

    # -------------------------------------
    # PANTALLA: MENU PRINCIPAL
    # -------------------------------------
    if pantalla_actual == "menu":

        ret, fotograma = video.read()

        if not ret:
            video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, fotograma = video.read()

        if ret:
            fotograma = cv2.cvtColor(
                fotograma, cv2.COLOR_BGR2RGB
            )

            fotograma = cv2.resize(
                fotograma, (ancho, alto)
            )

            fondo_video = pygame.surfarray.make_surface(
                fotograma.swapaxes(0, 1)
            )

            pantalla.blit(fondo_video, (0, 0))

        raton = pygame.mouse.get_pos()

        # BOTON INICIAR
        color_iniciar = (
            verde_claro
            if boton_iniciar.collidepoint(raton)
            else verde_oscuro
        )

        pygame.draw.rect(
            pantalla, color_iniciar, boton_iniciar,
            border_radius=12
        )

        texto = fuente.render(
            "INICIAR JUEGO", True, blanco
        )

        pantalla.blit(
            texto, texto.get_rect(center=boton_iniciar.center)
        )

        # BOTON SALIR
        color_salir = (
            negro_grisaceo
            if boton_salir.collidepoint(raton)
            else negro
        )

        pygame.draw.rect(
            pantalla, color_salir, boton_salir,
            border_radius=12
        )

        texto = fuente.render("SALIR", True, rojo)

        pantalla.blit(
            texto, texto.get_rect(center=boton_salir.center)
        )

    # -------------------------------------
    # PANTALLA: CONFIGURACION
    # -------------------------------------
    elif pantalla_actual == "configuracion":

        pantalla.fill(negro_grisaceo)

        # TITULO
        titulo = fuente_titulo.render(
            "CONFIGURAR PARTIDA", True, blanco
        )

        pantalla.blit(
            titulo,
            titulo.get_rect(center=(ancho // 2, 65))
        )

        # NOMBRE DEL ENEMIGO
        etiqueta = fuente_pequena.render(
            "Nombre del enemigo:", True, blanco
        )

        pantalla.blit(etiqueta, (300, 135))

        color_campo = (
            verde_claro if campo_activo else gris
        )

        pygame.draw.rect(
            pantalla, color_campo, campo_nombre,
            width=2, border_radius=6
        )

        texto_nombre = fuente_pequena.render(
            nombre_enemigo, True, blanco
        )

        pantalla.blit(
            texto_nombre,
            (campo_nombre.x + 10, campo_nombre.y + 12)
        )

        # QUIEN ATACA PRIMERO
        etiqueta = fuente_pequena.render(
            "¿Quien ataca primero?", True, blanco
        )

        pantalla.blit(etiqueta, (300, 245))

        # BOTON TU
        color_tu = (
            verde_claro
            if primer_atacante == "Tu"
            else negro
        )

        pygame.draw.rect(
            pantalla, color_tu, boton_tu,
            border_radius=8
        )

        texto_tu = fuente_pequena.render(
            "TU", True, blanco
        )

        pantalla.blit(
            texto_tu,
            texto_tu.get_rect(center=boton_tu.center)
        )

        # BOTON ENEMIGO
        color_enemigo = (
            verde_claro
            if primer_atacante == "Enemigo"
            else negro
        )

        pygame.draw.rect(
            pantalla, color_enemigo, boton_enemigo,
            border_radius=8
        )

        texto_enemigo = fuente_pequena.render(
            "ENEMIGO", True, blanco
        )

        pantalla.blit(
            texto_enemigo,
            texto_enemigo.get_rect(center=boton_enemigo.center)
        )

        # INFORMACION PERSONALIZABLE
        pygame.draw.rect(
            pantalla, negro, (200, 365, 600, 135),
            border_radius=8
        )

        lineas = informacion_partida.split("\n")

        for i, linea in enumerate(lineas):
            texto_info = fuente_pequena.render(
                linea, True, blanco
            )

            pantalla.blit(
                texto_info,
                texto_info.get_rect(
                    center=(ancho // 2, 390 + i * 28)
                )
            )

        raton = pygame.mouse.get_pos()

        # BOTON VOLVER
        color_volver = (
            rojo if boton_volver.collidepoint(raton)
            else (120, 25, 25)
        )

        pygame.draw.rect(
            pantalla, color_volver, boton_volver,
            border_radius=10
        )

        texto_volver = fuente_pequena.render(
            "VOLVER", True, blanco
        )

        pantalla.blit(
            texto_volver,
            texto_volver.get_rect(center=boton_volver.center)
        )

        # BOTON ACEPTAR
        color_aceptar = (
            verde_claro
            if boton_aceptar.collidepoint(raton)
            else verde_oscuro
        )

        pygame.draw.rect(
            pantalla, color_aceptar, boton_aceptar,
            border_radius=10
        )

        texto_aceptar = fuente_pequena.render(
            "ACEPTAR Y JUGAR", True, blanco
        )

        pantalla.blit(
            texto_aceptar,
            texto_aceptar.get_rect(center=boton_aceptar.center)
        )

    # -------------------------------------
    # PANTALLA: CARGA
    # -------------------------------------
    elif pantalla_actual == "carga":

        tiempo_actual = pygame.time.get_ticks()

        tiempo_transcurrido = (
            tiempo_actual - tiempo_inicio_carga
        )

        # CAMBIAR AL VIDEO DE CARGA A LOS 3 SEGUNDOS
        if tiempo_transcurrido >= 3000 and not video_cambiado:

            video_carga.set(cv2.CAP_PROP_POS_FRAMES, 0)

            video_actual = video_carga
            fps_actual = fps_carga

            tiempo_inicio_video_carga = tiempo_actual
            video_cambiado = True

        # MOSTRAR EL VIDEO ACTUAL
        ret, fotograma = video_actual.read()

        if not ret:
            video_actual.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, fotograma = video_actual.read()

        if ret:
            fotograma = cv2.cvtColor(
                fotograma, cv2.COLOR_BGR2RGB
            )

            fotograma = cv2.resize(
                fotograma, (ancho, alto)
            )

            fondo_video = pygame.surfarray.make_surface(
                fotograma.swapaxes(0, 1)
            )

            pantalla.blit(fondo_video, (0, 0))

        # CARGA DURANTE 6 SEGUNDOS DESDE EL CAMBIO DE VIDEO
        if (
            video_cambiado
            and tiempo_actual - tiempo_inicio_video_carga >= 6000
        ):

            sonido_barco.stop()
            pantalla_actual = "juego"

            print("Partida preparada")
            print("Enemigo:", nombre_enemigo)
            print("Primer atacante:", primer_atacante)

    # -------------------------------------
    # PANTALLA: JUEGO
    # -------------------------------------
    elif pantalla_actual == "juego":

        pantalla.blit(fondo_juego, (0, 0))

        # Aqui añadiremos el tablero y la logica de la partida.

    # ACTUALIZAR VENTANA
    pygame.display.flip()

    # CONTROLAR FPS
    reloj.tick(fps_actual)

# CERRAR RECURSOS
sonido_barco.stop()
video.release()
video_carga.release()

pygame.quit()
