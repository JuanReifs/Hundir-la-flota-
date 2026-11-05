"""
main.py
-------
Interfaz gráfica principal del juego Hundir la Flota (Battleship) usando Pygame.
Contiene las tres pantallas del juego (menú, configuración y combate) y toda
la lógica de dibujado: tableros, sprites de barcos, miras, botones y efectos.

Autores (Integrantes del grupo DAM2 - Acceso a Datos - CES Juan Pablo II):
- Integrante 1: Tablero propio, barcos y generación aleatoria (flota.py)
- Integrante 2: Interfaz gráfica Pygame, menús y recursos multimedia (main.py)
- Integrante 3: Tablero de ataques rival, controlador e IA de radar (ataques.py, pistas.py, partida.py)

Reglas de juego implementadas:
1. ATACAR AL RIVAL: se selecciona una casilla en el radar y se indica el resultado
   que comunica el rival (Agua, Tocado o Hundido).
   - Sin propagación automática: cada casilla se marca de forma individual.
   - HUNDIDO no salta turno; AGUA y TOCADO sí cambian de turno automáticamente.
2. ATAQUE RECIBIDO: se indica dónde ha disparado el rival y el programa calcula
   automáticamente si ha sido Agua, Tocado o Hundido en nuestra flota.
3. Visualización de mapas con sprites reales de barcos, miras de disparo e info.
4. Guardar/Cargar partida en formato JSON (módulo de Acceso a Datos).
"""

import os
import sys
import time

try:
    import pygame
except ImportError:
    print("\n" + "=" * 65)
    print(" [!] ERROR: Pygame no está instalado en este entorno de Python.")
    print(" Para instalar las dependencias necesarias ejecuta en la terminal:")
    print("     pip install -r requirements.txt")
    print(" O si usas pip directamente:")
    print("     pip install pygame-ce opencv-python")
    print("=" * 65 + "\n")
    sys.exit(1)

try:
    import cv2
    HAY_CV2 = True
except ImportError:
    HAY_CV2 = False

from constantes import (
    TAMANO,
    DESCONOCIDO,
    AGUA,
    TOCADO,
    HUNDIDO,
    RES_AGUA,
    RES_TOCADO,
    RES_HUNDIDO,
    TURNO_YO,
    TURNO_RIVAL,
    ESTADO_EN_CURSO,
    ESTADO_VICTORIA,
    ESTADO_DERROTA,
    ARCHIVO_GUARDADO,
    coord_a_texto,
)
from flota import Flota
from partida import Partida, JuegoError, TurnoIncorrecto, PartidaTerminada


# Directorio raíz del proyecto (donde reside main.py)
DIR_BASE = os.path.dirname(os.path.abspath(__file__))

# -----------------------------------------------------------------------------
# 1. LOCALIZADOR ROBUSTO DE RECURSOS (insensible a mayúsculas/minúsculas y rutas relativas)
# -----------------------------------------------------------------------------
def encontrar_recurso(ruta_relativa):
    """
    Busca un archivo ignorando mayúsculas/minúsculas y asegurando que la ruta
    se resuelva relativa al directorio raíz del proyecto (DIR_BASE).
    Esto permite ejecutar el juego desde cualquier IDE, terminal o carpeta.
    """
    # 1. Intentar ruta directa relativa a DIR_BASE
    candidato = os.path.join(DIR_BASE, ruta_relativa)
    if os.path.exists(candidato):
        return candidato
    if os.path.exists(ruta_relativa):
        return os.path.abspath(ruta_relativa)

    # 2. Búsqueda insensible a mayúsculas/minúsculas recorriendo subdirectorios
    partes = os.path.normpath(ruta_relativa).split(os.sep)
    actual = DIR_BASE
    for parte in partes:
        if not os.path.exists(actual):
            return None
        coincidencia = None
        for entrada in os.listdir(actual):
            if entrada.lower() == parte.lower():
                coincidencia = entrada
                break
        if coincidencia is None:
            return None
        actual = os.path.join(actual, coincidencia)
    return actual


# -----------------------------------------------------------------------------
# 2. INICIALIZACIÓN DE PYGAME Y PANTALLA
# -----------------------------------------------------------------------------
pygame.init()

HAY_AUDIO = False
try:
    pygame.mixer.init()
    HAY_AUDIO = True
except Exception as e:
    print("Aviso: No se pudo inicializar audio:", e)

# Reservar 2 canales: el 0 para la música interna de SDL, el 1 para efectos
canal_efectos = None
if HAY_AUDIO:
    try:
        pygame.mixer.set_num_channels(8)       # 8 canales disponibles en total
        pygame.mixer.set_reserved(1)           # reservar canal 0 para que no lo use .play()
        canal_efectos = pygame.mixer.Channel(1) # nuestros efectos van por el canal 1
    except Exception:
        canal_efectos = None

# Resolución de la ventana de juego
ANCHO = 1200
ALTO = 760
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("BATTLESHIP · Hundir la Flota (DAM2 - Acceso a Datos)")
reloj = pygame.time.Clock()


# -----------------------------------------------------------------------------
# 3. PALETA DE COLORES
# -----------------------------------------------------------------------------
C_FONDO        = (10,  18,  30)
C_PANEL        = (16,  28,  46)
C_PANEL_BORDE  = (30,  56,  88)
C_PANEL_CLARO  = (22,  38,  62)

C_BLANCO       = (245, 245, 250)
C_NEGRO        = (0,   0,   0)
C_GRIS         = (120, 130, 145)
C_GRIS_CLARO   = (190, 205, 220)
C_AZUL_AGUA    = (18,  48,  78)
C_AZUL_BORDE   = (38,  88, 130)

C_VERDE_BOTON  = (28,  110, 65)
C_VERDE_HOVER  = (40,  150, 90)
C_ROJO_BOTON   = (145, 35,  35)
C_ROJO_HOVER   = (195, 45,  45)
C_AZUL_BOTON   = (25,  75, 125)
C_AZUL_HOVER   = (35, 105, 175)

C_AMARILLO     = (255, 215,  30)   # tocado
C_ROJO_HUNDIDO = (235,  45,  45)   # hundido
C_AZUL_IMPACTO = (70,  160, 245)   # agua impactada
C_MIRA         = (255, 220,   0)   # mira objetivo
C_NARANJA      = (255, 140,   0)   # aviso / notificaciones


# -----------------------------------------------------------------------------
# 4. TIPOGRAFÍAS
# -----------------------------------------------------------------------------
fuente_titulo    = pygame.font.SysFont("arial", 30, bold=True)
fuente_subtitulo = pygame.font.SysFont("arial", 17, bold=True)
fuente_seccion   = pygame.font.SysFont("arial", 15, bold=True)
fuente_normal    = pygame.font.SysFont("arial", 14)
fuente_pequena   = pygame.font.SysFont("arial", 12)
fuente_tablero   = pygame.font.SysFont("consolas", 13, bold=True)
fuente_impacto   = pygame.font.SysFont("arial", 18, bold=True)


# -----------------------------------------------------------------------------
# 5. CARGA DE RECURSOS MULTIMEDIA
# -----------------------------------------------------------------------------
def cargar_imagen(ruta_relativa):
    """Carga una imagen desde disco; devuelve None si no existe o falla."""
    ruta = encontrar_recurso(ruta_relativa)
    if ruta and os.path.exists(ruta):
        try:
            return pygame.image.load(ruta).convert_alpha()
        except Exception as e:
            print(f"Error cargando imagen {ruta}: {e}")
    return None


img_fondo_inicio = cargar_imagen("Recursos/Imagenes/inicio.png")
if img_fondo_inicio:
    img_fondo_inicio = pygame.transform.scale(img_fondo_inicio, (ANCHO, ALTO))

img_fondo_juego = cargar_imagen("Recursos/Imagenes/juego.png")
if img_fondo_juego:
    img_fondo_juego = pygame.transform.scale(img_fondo_juego, (ANCHO, ALTO))

# ------------------------------------------------------------------
# Sprites de barcos: las imágenes son siempre HORIZONTALES (barco
# apuntando hacia la derecha). Las recortamos con get_bounding_rect()
# para eliminar el relleno transparente y quedarnos solo con el
# contenido real del sprite.
# ------------------------------------------------------------------
sprites_barcos_h = {}   # versión horizontal (original recortada)
sprites_barcos_v = {}   # versión vertical (rotada 90°)

for tam in range(1, 5):
    img_raw = cargar_imagen(f"Recursos/Imagenes/Barco-{tam}.png")
    if img_raw:
        try:
            bbox = img_raw.get_bounding_rect()
            img_recortada = img_raw.subsurface(bbox)
        except Exception:
            img_recortada = img_raw
        sprites_barcos_h[tam] = img_recortada
        # El barco vertical es el horizontal rotado 90° en sentido antihorario
        sprites_barcos_v[tam] = pygame.transform.rotate(img_recortada, 90)
    else:
        sprites_barcos_h[tam] = None
        sprites_barcos_v[tam] = None


def cargar_sonido(ruta_relativa, volumen=0.6):
    """Carga un efecto de sonido desde disco; devuelve None si falla."""
    if not HAY_AUDIO:
        return None
    ruta = encontrar_recurso(ruta_relativa)
    if ruta and os.path.exists(ruta):
        try:
            snd = pygame.mixer.Sound(ruta)
            snd.set_volume(volumen)
            return snd
        except Exception:
            pass
    return None


# El sonido del botón de inicio se elimina por petición expresa
snd_boton = None

# Efecto de sonido al hundir un barco
snd_barco = cargar_sonido("Recursos/Sonidos/barco.mp3", 0.7)


# Ruta de la música que ya está cargada. Si coincide con lo que se pide,
# no volvemos a hacer load() para evitar que la pista se solape consigo misma.
_musica_cargada = None


def asegurar_musica(ruta="Recursos/Sonidos/inicio.mp3", volumen=0.35):
    """
    Garantiza que la música de fondo suene en bucle continuo sin solapamientos.

    Se guarda la ruta que ya fue cargada en _musica_cargada. Si la música ya
    está sonando con la misma pista, no hace nada. Esto evita que 60 llamadas
    por segundo (una por frame) recarguen y dupliquen el audio.
    Solo vuelve a cargar si se solicita una pista distinta.
    """
    global _musica_cargada
    if not HAY_AUDIO:
        return
    try:
        ruta_real = encontrar_recurso(ruta)
        if not (ruta_real and os.path.exists(ruta_real)):
            return

        # Si ya está sonando la misma pista, no hacer nada
        if pygame.mixer.music.get_busy() and _musica_cargada == ruta_real:
            return

        # Parar cualquier reproducción anterior antes de cargar la nueva
        pygame.mixer.music.stop()
        pygame.mixer.music.load(ruta_real)
        pygame.mixer.music.set_volume(volumen)
        pygame.mixer.music.play(-1)  # -1 = bucle infinito
        _musica_cargada = ruta_real
    except Exception as e:
        print("Aviso música:", e)


def sonar(sonido):
    """
    Reproduce un efecto de sonido por el canal reservado (canal 1).
    Si ya hay un efecto sonando en ese canal, lo para primero para
    evitar que se solapen varios efectos entre sí.
    La música de fondo (que va por pygame.mixer.music) no se ve afectada.
    """
    global canal_efectos
    if not (HAY_AUDIO and sonido):
        return
    try:
        if canal_efectos is not None:
            canal_efectos.stop()   # parar el efecto anterior si aún suena
            canal_efectos.play(sonido)
        else:
            sonido.play()
    except Exception:
        pass


def abrir_video(ruta_relativa):
    """Abre un vídeo con OpenCV para usarlo como fondo animado."""
    if not HAY_CV2:
        return None
    ruta = encontrar_recurso(ruta_relativa)
    if ruta and os.path.exists(ruta):
        cap = cv2.VideoCapture(ruta)
        if cap.isOpened():
            return cap
    return None


def dibujar_fotograma_video(captura):
    """Dibuja el siguiente fotograma del vídeo en la pantalla; hace loop al llegar al final."""
    if not captura:
        return False
    ok, frame = captura.read()
    if not ok:
        captura.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ok, frame = captura.read()
    if ok:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (ANCHO, ALTO))
        superficie = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        pantalla.blit(superficie, (0, 0))
        return True
    return False


# -----------------------------------------------------------------------------
# 6. UTILIDADES GRÁFICAS
# -----------------------------------------------------------------------------
def dibujar_texto(texto, fuente, color, x, y, centrar=False):
    """Dibuja un texto en pantalla. Si centrar=True, x e y son el centro."""
    sup = fuente.render(str(texto), True, color)
    rect = sup.get_rect(center=(x, y)) if centrar else sup.get_rect(topleft=(x, y))
    pantalla.blit(sup, rect)
    return rect


def dibujar_boton(rect, texto, color_base=C_AZUL_BOTON, color_hover=C_AZUL_HOVER,
                  activo=True, seleccionado=False):
    """
    Dibuja un botón con efecto hover y estado seleccionado/inactivo.
    Devuelve True si el cursor está sobre él (hover).
    """
    pos_raton = pygame.mouse.get_pos()
    colision = rect.collidepoint(pos_raton)

    if not activo:
        color = C_GRIS
    elif seleccionado:
        color = C_VERDE_BOTON
    elif colision:
        color = color_hover
    else:
        color = color_base

    pygame.draw.rect(pantalla, color, rect, border_radius=6)
    borde = C_BLANCO if (colision or seleccionado) else C_PANEL_BORDE
    pygame.draw.rect(pantalla, borde, rect, width=2, border_radius=6)
    dibujar_texto(texto, fuente_normal, C_BLANCO, rect.centerx, rect.centery, centrar=True)
    return colision and activo


def dibujar_barco_sprite(barco, origen_x, origen_y, tam_celda):
    """
    Dibuja el sprite real del barco en el tablero.
    - Si el barco es horizontal usa sprites_barcos_h[tam].
    - Si el barco es vertical usa sprites_barcos_v[tam] (pre-rotado 90°).
    El sprite se escala exactamente al área de las celdas ocupadas.
    """
    tam = barco["tamano"]
    coords = barco["coordenadas"]

    filas = [c[0] for c in coords]
    cols  = [c[1] for c in coords]
    f_min, f_max = min(filas), max(filas)
    c_min, c_max = min(cols),  max(cols)

    es_horizontal = (f_min == f_max)

    # Margen interior de 2 píxeles para no pegar el sprite al borde de la celda
    margen = 2
    rx = origen_x + c_min * tam_celda + margen
    ry = origen_y + f_min * tam_celda + margen

    if es_horizontal:
        ancho_px = len(coords) * tam_celda - margen * 2
        alto_px  = tam_celda - margen * 2
        sprite = sprites_barcos_h.get(tam)
    else:
        ancho_px = tam_celda - margen * 2
        alto_px  = len(coords) * tam_celda - margen * 2
        sprite = sprites_barcos_v.get(tam)

    if sprite:
        try:
            img_escalada = pygame.transform.smoothscale(sprite, (ancho_px, alto_px))
            pantalla.blit(img_escalada, (rx, ry))
        except Exception:
            # Fallback: rectángulo de color si el escalado falla
            pygame.draw.rect(pantalla, (50, 95, 120), (rx, ry, ancho_px, alto_px), border_radius=3)
    else:
        pygame.draw.rect(pantalla, (50, 95, 120), (rx, ry, ancho_px, alto_px), border_radius=3)


def dibujar_mira(rx, ry, tam_celda, color=C_MIRA):
    """Dibuja una mira telemétrica en las esquinas de la celda apuntada."""
    g = 3   # grosor línea
    L = 8   # largo del trazo en la esquina
    # Esquina superior-izquierda
    pygame.draw.line(pantalla, color, (rx,            ry),            (rx + L, ry),            g)
    pygame.draw.line(pantalla, color, (rx,            ry),            (rx,     ry + L),         g)
    # Esquina superior-derecha
    pygame.draw.line(pantalla, color, (rx + tam_celda, ry),           (rx + tam_celda - L, ry), g)
    pygame.draw.line(pantalla, color, (rx + tam_celda, ry),           (rx + tam_celda, ry + L), g)
    # Esquina inferior-izquierda
    pygame.draw.line(pantalla, color, (rx,            ry + tam_celda), (rx + L, ry + tam_celda), g)
    pygame.draw.line(pantalla, color, (rx,            ry + tam_celda), (rx,     ry + tam_celda - L), g)
    # Esquina inferior-derecha
    pygame.draw.line(pantalla, color, (rx + tam_celda, ry + tam_celda), (rx + tam_celda - L, ry + tam_celda), g)
    pygame.draw.line(pantalla, color, (rx + tam_celda, ry + tam_celda), (rx + tam_celda,     ry + tam_celda - L), g)
    # Cruz central
    cx, cy = rx + tam_celda // 2, ry + tam_celda // 2
    pygame.draw.line(pantalla, color, (cx - 5, cy), (cx + 5, cy), 2)
    pygame.draw.line(pantalla, color, (cx, cy - 5), (cx, cy + 5), 2)


def reproducir_transicion(ruta_video, duracion=2.0):
    """Muestra una breve animación de transición antes de entrar al combate."""
    sonar(snd_barco)
    cap = abrir_video(ruta_video)
    inicio = time.time()

    while time.time() - inicio < duracion:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                if cap:
                    cap.release()
                pygame.quit()
                sys.exit()

        if not (cap and dibujar_fotograma_video(cap)):
            pantalla.fill(C_FONDO)
            progreso = int((time.time() - inicio) / duracion * 100)
            dibujar_texto("PREPARANDO FLOTA PARA EL COMBATE...", fuente_titulo,
                          C_BLANCO, ANCHO // 2, ALTO // 2 - 30, centrar=True)
            pygame.draw.rect(pantalla, C_PANEL_BORDE,
                             (ANCHO // 2 - 200, ALTO // 2 + 20, 400, 22), border_radius=10)
            pygame.draw.rect(pantalla, C_VERDE_HOVER,
                             (ANCHO // 2 - 200, ALTO // 2 + 20, int(4 * progreso), 22), border_radius=10)

        pygame.display.flip()
        reloj.tick(30)

    if cap:
        cap.release()


# -----------------------------------------------------------------------------
# 7. PANTALLA 1: MENÚ PRINCIPAL
# -----------------------------------------------------------------------------
def pantalla_menu():
    """Pantalla de inicio con fondo animado y tres opciones."""
    asegurar_musica()
    captura_video = abrir_video("Recursos/Videos/Inicio.mp4")

    btn_iniciar = pygame.Rect(ANCHO // 2 - 160, 350, 320, 52)
    btn_cargar  = pygame.Rect(ANCHO // 2 - 160, 418, 320, 52)
    btn_salir   = pygame.Rect(ANCHO // 2 - 160, 486, 320, 52)

    while True:
        asegurar_musica()

        if captura_video and dibujar_fotograma_video(captura_video):
            pass
        elif img_fondo_inicio:
            pantalla.blit(img_fondo_inicio, (0, 0))
        else:
            pantalla.fill(C_FONDO)

        # Panel central semitransparente
        panel = pygame.Surface((460, 400), pygame.SRCALPHA)
        panel.fill((10, 20, 35, 220))
        pantalla.blit(panel, (ANCHO // 2 - 230, 190))
        pygame.draw.rect(pantalla, C_PANEL_BORDE, (ANCHO // 2 - 230, 190, 460, 400),
                         width=2, border_radius=12)

        dibujar_texto("BATTLESHIP", fuente_titulo, C_BLANCO, ANCHO // 2, 225, centrar=True)
        dibujar_texto("Proyecto DAM2  ·  Hundir la Flota", fuente_subtitulo,
                      C_GRIS_CLARO, ANCHO // 2, 265, centrar=True)
        dibujar_texto("Asignatura: Acceso a Datos  ·  CES Juan Pablo II",
                      fuente_pequena, C_AMARILLO, ANCHO // 2, 295, centrar=True)

        hay_guardado = os.path.exists(ARCHIVO_GUARDADO)
        dibujar_boton(btn_iniciar, "1.  Nueva Partida", C_AZUL_BOTON, C_AZUL_HOVER)
        dibujar_boton(btn_cargar,  "2.  Cargar Partida (JSON)", C_VERDE_BOTON, C_VERDE_HOVER,
                      activo=hay_guardado)
        dibujar_boton(btn_salir,   "3.  Salir", C_ROJO_BOTON, C_ROJO_HOVER)

        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                if captura_video:
                    captura_video.release()
                pygame.quit()
                sys.exit()

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if btn_iniciar.collidepoint(ev.pos):
                    if captura_video:
                        captura_video.release()
                    pantalla_configuracion()
                    return

                elif hay_guardado and btn_cargar.collidepoint(ev.pos):
                    try:
                        partida_cargada = Partida.cargar_de_fichero(ARCHIVO_GUARDADO)
                        if captura_video:
                            captura_video.release()
                        reproducir_transicion("Recursos/Videos/cargando.mp4", 1.8)
                        pantalla_juego(partida_cargada)
                        return
                    except Exception as err:
                        print("Error al cargar la partida guardada:", err)

                elif btn_salir.collidepoint(ev.pos):
                    if captura_video:
                        captura_video.release()
                    pygame.quit()
                    sys.exit()

        reloj.tick(60)


# -----------------------------------------------------------------------------
# 8. PANTALLA 2: CONFIGURACIÓN
# -----------------------------------------------------------------------------
def pantalla_configuracion():
    """
    Pantalla para introducir nombres, elegir quién ataca primero
    y previsualizar la flota generada aleatoriamente con sprites reales.
    """
    asegurar_musica()

    nombre_jugador = "Comandante"
    nombre_enemigo = "Almirante Rival"
    empiezo_yo = True
    campo_activo = "enemigo"
    flota_actual = Flota()

    # ---- Zonas de texto ----
    campo_jug = pygame.Rect(145, 175, 310, 36)
    campo_ene = pygame.Rect(145, 255, 310, 36)

    # ---- Botones ----
    btn_yo      = pygame.Rect(145, 330, 148, 38)
    btn_rival   = pygame.Rect(303, 330, 148, 38)
    btn_regen   = pygame.Rect(145, 390, 310, 40)
    btn_comenzar= pygame.Rect(145, 448, 310, 50)
    btn_volver  = pygame.Rect(145, 516, 310, 38)

    # ---- Tablero de previsualización ----
    PX = 530       # origen X del tablero preview
    PY = 110       # origen Y del tablero preview
    TC = 36        # tamaño de cada celda en el preview

    while True:
        asegurar_musica()

        if img_fondo_inicio:
            pantalla.blit(img_fondo_inicio, (0, 0))
        else:
            pantalla.fill(C_FONDO)

        # ---- Panel izquierdo (configuración) ----
        pygame.draw.rect(pantalla, (16, 28, 46, 235),
                         pygame.Rect(80, 40, 420, 530), border_radius=12)
        pygame.draw.rect(pantalla, C_PANEL_BORDE,
                         pygame.Rect(80, 40, 420, 530), width=2, border_radius=12)

        dibujar_texto("CONFIGURACIÓN", fuente_titulo, C_BLANCO, 290, 70, centrar=True)
        dibujar_texto("Ajusta tu batalla naval antes de zarpar",
                      fuente_pequena, C_GRIS_CLARO, 290, 100, centrar=True)

        # Campo nombre jugador
        dibujar_texto("Tu Nombre:", fuente_normal, C_BLANCO, 145, 152)
        pygame.draw.rect(pantalla, (235, 240, 250), campo_jug, border_radius=5)
        pygame.draw.rect(pantalla, C_VERDE_HOVER if campo_activo == "jugador" else C_GRIS,
                         campo_jug, width=2, border_radius=5)
        dibujar_texto(nombre_jugador, fuente_normal, C_NEGRO, campo_jug.x + 8, campo_jug.y + 9)

        # Campo nombre rival
        dibujar_texto("Nombre del Rival:", fuente_normal, C_BLANCO, 145, 232)
        pygame.draw.rect(pantalla, (235, 240, 250), campo_ene, border_radius=5)
        pygame.draw.rect(pantalla, C_VERDE_HOVER if campo_activo == "enemigo" else C_GRIS,
                         campo_ene, width=2, border_radius=5)
        dibujar_texto(nombre_enemigo, fuente_normal, C_NEGRO, campo_ene.x + 8, campo_ene.y + 9)

        # Selector de turno
        dibujar_texto("¿Quién ataca primero?", fuente_normal, C_BLANCO, 145, 308)
        dibujar_boton(btn_yo,    "Yo (Opción 1)",    C_AZUL_BOTON, C_AZUL_HOVER, seleccionado=empiezo_yo)
        dibujar_boton(btn_rival, "Rival (Opción 2)", C_AZUL_BOTON, C_AZUL_HOVER, seleccionado=(not empiezo_yo))

        dibujar_boton(btn_regen,    "Generar Otra Flota", C_AZUL_BOTON,  C_AZUL_HOVER)
        dibujar_boton(btn_comenzar, "Zarpar a la Batalla!", C_VERDE_BOTON, C_VERDE_HOVER)
        dibujar_boton(btn_volver,   "Volver al Menu",        C_ROJO_BOTON,  C_ROJO_HOVER)

        # ---- Panel derecho (previsualización de la flota) ----
        ancho_panel_der = TC * 10 + 60
        pygame.draw.rect(pantalla, (16, 28, 46, 235),
                         pygame.Rect(PX - 30, 40, ancho_panel_der + 30, 680),
                         border_radius=12)
        pygame.draw.rect(pantalla, C_PANEL_BORDE,
                         pygame.Rect(PX - 30, 40, ancho_panel_der + 30, 680),
                         width=2, border_radius=12)

        cx_der = PX - 30 + (ancho_panel_der + 30) // 2
        dibujar_texto("TU FLOTA DESPLEGADA", fuente_subtitulo, C_BLANCO, cx_der, 68, centrar=True)
        dibujar_texto("1x4  ·  2x3  ·  3x2  ·  4x1  (Generación aleatoria)",
                      fuente_pequena, C_GRIS_CLARO, cx_der, 92, centrar=True)

        # Números de fila y columna del tablero preview
        for c in range(10):
            dibujar_texto(str(c), fuente_tablero, C_AMARILLO,
                          PX + c * TC + TC // 2, PY - 14, centrar=True)
        for f in range(10):
            dibujar_texto(str(f), fuente_tablero, C_AMARILLO,
                          PX - 16, PY + f * TC + TC // 2, centrar=True)

        # Celdas del tablero
        for f in range(10):
            for c in range(10):
                rx = PX + c * TC
                ry = PY + f * TC
                pygame.draw.rect(pantalla, C_AZUL_AGUA, (rx, ry, TC, TC))
                pygame.draw.rect(pantalla, C_AZUL_BORDE, (rx, ry, TC, TC), width=1)

        # Sprites de los barcos
        for barco in flota_actual.barcos:
            dibujar_barco_sprite(barco, PX, PY, TC)

        # Leyenda debajo del tablero
        ly = PY + 10 * TC + 18
        dibujar_texto("Leyenda:", fuente_seccion, C_BLANCO, PX - 20, ly)
        ly += 22
        for txt in [
            "Acorazado: 1 barco de 4 casillas",
            "Crucero:   2 barcos de 3 casillas",
            "Destructor:3 barcos de 2 casillas",
            "Lancha:    4 barcos de 1 casilla",
            "Total: 10 barcos  |  Sin diagonales",
        ]:
            dibujar_texto(txt, fuente_pequena, C_GRIS_CLARO, PX - 20, ly)
            ly += 18

        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if campo_jug.collidepoint(ev.pos):
                    campo_activo = "jugador"
                elif campo_ene.collidepoint(ev.pos):
                    campo_activo = "enemigo"
                elif btn_yo.collidepoint(ev.pos):
                    empiezo_yo = True
                elif btn_rival.collidepoint(ev.pos):
                    empiezo_yo = False
                elif btn_regen.collidepoint(ev.pos):
                    flota_actual = Flota()
                elif btn_comenzar.collidepoint(ev.pos):
                    nueva_partida = Partida(
                        tablero_propio=flota_actual,
                        nombre_jugador=nombre_jugador.strip() or "Jugador",
                        nombre_rival=nombre_enemigo.strip() or "Rival",
                        empiezo_yo=empiezo_yo,
                    )
                    reproducir_transicion("Recursos/Videos/cargando.mp4", 2.0)
                    pantalla_juego(nueva_partida)
                    return
                elif btn_volver.collidepoint(ev.pos):
                    pantalla_menu()
                    return

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_TAB:
                    campo_activo = "enemigo" if campo_activo == "jugador" else "jugador"
                elif campo_activo == "jugador":
                    if ev.key == pygame.K_BACKSPACE:
                        nombre_jugador = nombre_jugador[:-1]
                    elif len(nombre_jugador) < 18 and ev.unicode.isprintable():
                        nombre_jugador += ev.unicode
                elif campo_activo == "enemigo":
                    if ev.key == pygame.K_BACKSPACE:
                        nombre_enemigo = nombre_enemigo[:-1]
                    elif len(nombre_enemigo) < 18 and ev.unicode.isprintable():
                        nombre_enemigo += ev.unicode

        reloj.tick(60)


# -----------------------------------------------------------------------------
# 9. PANTALLA 3: COMBATE
# -----------------------------------------------------------------------------
def pantalla_juego(partida: Partida):
    """
    Pantalla principal de combate con layout reorganizado:

    ┌───────────────┬───────────────┬──────────────────────┐
    │  MI FLOTA     │ RADAR ATAQUES │  PANEL LATERAL       │
    │  10x10        │  10x10        │  Opción 1 (atacar)   │
    │  (tam_c=30px) │  (tam_c=30px) │  Opción 2 (recibir)  │
    ├───────────────┴───────────────┤  Otros botones       │
    │  PANEL INFERIOR               │                      │
    │  Estado flota · Historial     │                      │
    └───────────────────────────────┴──────────────────────┘

    Reglas:
    - HUNDIDO no salta turno; AGUA y TOCADO sí lo hacen.
    - Pulsar "Pasar turno" para ceder el turno al rival tras marcar hundidos.
    - Sin propagación automática (flood-fill) al marcar hundido.
    """
    asegurar_musica()

    # Tamaño de celda: 30 px × 10 celdas = 300 px por tablero
    TC = 30

    # Orígenes de los dos tableros
    OPX = 30          # tablero PROPIO: origen X
    OPY = 115         # tablero PROPIO: origen Y
    ORX = 370         # tablero RIVAL: origen X
    ORY = 115         # tablero RIVAL: origen Y

    # Coordenadas seleccionadas para disparar (mapa rival)
    dis_f, dis_c = 0, 0
    resultado_sel = RES_AGUA

    # Coordenadas seleccionadas para ataque recibido (mapa propio)
    rec_f, rec_c = 0, 0

    radar_activo = False
    casilla_sug = None
    info_radar = None

    msg = ("¡Partida iniciada!  " +
           ("Tu turno (Opción 1)." if partida.turno == TURNO_YO
            else f"Turno de {partida.nombre_rival} (Opción 2)."))
    msg_color = C_VERDE_HOVER

    # ---- Panel lateral derecho ----
    PL_X = 718          # panel lateral origen X
    PL_W = ANCHO - PL_X - 10  # ancho del panel lateral (~472 px)

    # Botones de resultado del disparo
    bw = PL_W // 3 - 4
    btn_agua    = pygame.Rect(PL_X + 4,          165, bw, 32)
    btn_tocado  = pygame.Rect(PL_X + 4 + bw + 4, 165, bw, 32)
    btn_hundido = pygame.Rect(PL_X + 4 + 2*(bw+4), 165, bw, 32)

    btn_confirmar  = pygame.Rect(PL_X + 4, 203, PL_W - 8, 34)
    btn_pasar      = pygame.Rect(PL_X + 4, 243, PL_W - 8, 32)

    # Separador opción 2
    btn_calcular   = pygame.Rect(PL_X + 4, 340, PL_W - 8, 36)

    # Botones inferiores
    btn_radar      = pygame.Rect(PL_X + 4, 420, PL_W - 8, 32)
    btn_deshacer   = pygame.Rect(PL_X + 4, 460, (PL_W - 12) // 2, 32)
    btn_guardar    = pygame.Rect(PL_X + 4 + (PL_W - 12) // 2 + 4, 460, (PL_W - 12) // 2, 32)
    btn_salir_menu = pygame.Rect(PL_X + 4, 500, PL_W - 8, 32)

    while True:
        asegurar_musica()

        # Fondo de juego
        if img_fondo_juego:
            pantalla.blit(img_fondo_juego, (0, 0))
        else:
            pantalla.fill(C_FONDO)

        # ==============================================================
        # CABECERA
        # ==============================================================
        pygame.draw.rect(pantalla, C_PANEL, (10, 8, ANCHO - 20, 46), border_radius=8)
        pygame.draw.rect(pantalla, C_PANEL_BORDE, (10, 8, ANCHO - 20, 46), width=2, border_radius=8)

        dibujar_texto("BATTLESHIP  ·  ACCESO A DATOS", fuente_subtitulo, C_BLANCO, 20, 24)

        # Badge de turno (centro de la cabecera)
        if partida.terminada:
            txt_t = "BATALLA FINALIZADA"
            c_badge = (60, 45, 15)
            c_txt_t = C_AMARILLO
        elif partida.turno == TURNO_YO:
            txt_t = f"TU TURNO ({partida.nombre_jugador})  -  Dispara en Opcion 1"
            c_badge = (20, 65, 40)
            c_txt_t = C_VERDE_HOVER
        else:
            txt_t = f"TURNO DE {partida.nombre_rival.upper()}  -  Ataque en Opcion 2"
            c_badge = (75, 25, 25)
            c_txt_t = C_ROJO_HOVER

        badge_w = 460
        badge_rect = pygame.Rect(ANCHO // 2 - badge_w // 2, 14, badge_w, 32)
        pygame.draw.rect(pantalla, c_badge, badge_rect, border_radius=5)
        pygame.draw.rect(pantalla, c_txt_t, badge_rect, width=2, border_radius=5)
        dibujar_texto(txt_t, fuente_seccion, c_txt_t, badge_rect.centerx, badge_rect.centery, centrar=True)

        dibujar_texto(f"Jugadas: {len(partida.historial)}", fuente_pequena,
                      C_GRIS_CLARO, ANCHO - 110, 25)

        # ==============================================================
        # TABLERO 1: MI FLOTA (izquierda)
        # ==============================================================
        ancho_tab = TC * 10
        panel_p = pygame.Rect(OPX - 24, 70, ancho_tab + 50, TC * 10 + 60)
        pygame.draw.rect(pantalla, C_PANEL, panel_p, border_radius=8)
        pygame.draw.rect(pantalla, C_PANEL_BORDE, panel_p, width=2, border_radius=8)

        cx_p = OPX + ancho_tab // 2
        dibujar_texto(f"MI FLOTA  ({partida.nombre_jugador})", fuente_seccion, C_BLANCO,
                      cx_p, 82, centrar=True)
        dibujar_texto("tus barcos e impactos recibidos", fuente_pequena, C_GRIS,
                      cx_p, 98, centrar=True)

        # Números de columna
        for c in range(TAMANO):
            dibujar_texto(str(c), fuente_tablero, C_AMARILLO,
                          OPX + c * TC + TC // 2, OPY - 12, centrar=True)
        # Celdas y números de fila
        for f in range(TAMANO):
            dibujar_texto(str(f), fuente_tablero, C_AMARILLO,
                          OPX - 16, OPY + f * TC + TC // 2, centrar=True)
            for c in range(TAMANO):
                rx = OPX + c * TC
                ry = OPY + f * TC
                pygame.draw.rect(pantalla, C_AZUL_AGUA, (rx, ry, TC, TC))
                pygame.draw.rect(pantalla, C_AZUL_BORDE, (rx, ry, TC, TC), width=1)

        # Sprites de los barcos propios
        for barco in partida.propio.barcos:
            dibujar_barco_sprite(barco, OPX, OPY, TC)

        # Marcas de impacto en el tablero propio
        for f in range(TAMANO):
            for c in range(TAMANO):
                rx = OPX + c * TC
                ry = OPY + f * TC
                impacto = partida.propio.disparos_recibidos.get((f, c))
                if impacto == RES_AGUA:
                    pygame.draw.circle(pantalla, C_AZUL_IMPACTO,
                                       (rx + TC // 2, ry + TC // 2), 5)
                elif impacto == RES_TOCADO:
                    dibujar_texto("X", fuente_impacto, C_AMARILLO,
                                  rx + TC // 2, ry + TC // 2, centrar=True)
                elif impacto == RES_HUNDIDO:
                    overlay = pygame.Surface((TC - 2, TC - 2), pygame.SRCALPHA)
                    overlay.fill((160, 20, 20, 150))
                    pantalla.blit(overlay, (rx + 1, ry + 1))
                    dibujar_texto("X", fuente_impacto, C_ROJO_HUNDIDO,
                                  rx + TC // 2, ry + TC // 2, centrar=True)

        # Mira en la casilla del ataque recibido
        if partida.turno == TURNO_RIVAL and not partida.terminada:
            dibujar_mira(OPX + rec_c * TC, OPY + rec_f * TC, TC, C_ROJO_HOVER)

        # ==============================================================
        # TABLERO 2: RADAR DE ATAQUES (centro)
        # ==============================================================
        panel_r = pygame.Rect(ORX - 24, 70, ancho_tab + 50, TC * 10 + 60)
        pygame.draw.rect(pantalla, C_PANEL, panel_r, border_radius=8)
        pygame.draw.rect(pantalla, C_PANEL_BORDE, panel_r, width=2, border_radius=8)

        cx_r = ORX + ancho_tab // 2
        dibujar_texto(f"RADAR ATAQUES  ({partida.nombre_rival})", fuente_seccion, C_BLANCO,
                      cx_r, 82, centrar=True)
        dibujar_texto("tus disparos al enemigo", fuente_pequena, C_GRIS,
                      cx_r, 98, centrar=True)

        for c in range(TAMANO):
            dibujar_texto(str(c), fuente_tablero, C_AMARILLO,
                          ORX + c * TC + TC // 2, ORY - 12, centrar=True)

        for f in range(TAMANO):
            dibujar_texto(str(f), fuente_tablero, C_AMARILLO,
                          ORX - 16, ORY + f * TC + TC // 2, centrar=True)
            for c in range(TAMANO):
                rx = ORX + c * TC
                ry = ORY + f * TC
                rect_celda = pygame.Rect(rx, ry, TC, TC)
                estado = partida.ataques.estado(f, c)

                # Color del calor del radar IA
                if radar_activo and info_radar and estado == DESCONOCIDO:
                    prob = info_radar["mapa_calor"][f][c]
                    if prob > 0:
                        col_calor = (int(16 + 210 * prob), int(55 + 180 * prob), 45)
                        pygame.draw.rect(pantalla, col_calor, rect_celda)
                    else:
                        pygame.draw.rect(pantalla, (12, 28, 48), rect_celda)
                else:
                    pygame.draw.rect(pantalla, (14, 32, 54), rect_celda)

                pygame.draw.rect(pantalla, C_AZUL_BORDE, rect_celda, width=1)

                # Casilla sugerida por el radar IA
                if radar_activo and casilla_sug == (f, c) and estado == DESCONOCIDO:
                    pygame.draw.rect(pantalla, C_VERDE_HOVER, rect_celda, width=2)
                    dibujar_texto("?", fuente_impacto, C_VERDE_HOVER,
                                  rect_celda.centerx, rect_celda.centery, centrar=True)

                # Marcas de los disparos realizados
                if estado == AGUA:
                    pygame.draw.circle(pantalla, C_AZUL_IMPACTO, rect_celda.center, 5)
                elif estado == TOCADO:
                    dibujar_texto("X", fuente_impacto, C_AMARILLO,
                                  rect_celda.centerx, rect_celda.centery, centrar=True)
                elif estado == HUNDIDO:
                    pygame.draw.rect(pantalla, (85, 20, 20), rect_celda)
                    dibujar_texto("X", fuente_impacto, C_ROJO_HUNDIDO,
                                  rect_celda.centerx, rect_celda.centery, centrar=True)

        # Mira en la casilla objetivo del próximo disparo
        dibujar_mira(ORX + dis_c * TC, ORY + dis_f * TC, TC, C_MIRA)

        # ==============================================================
        # PANEL LATERAL DERECHO
        # ==============================================================
        pygame.draw.rect(pantalla, C_PANEL,
                         pygame.Rect(PL_X - 4, 70, PL_W + 14, 500), border_radius=8)
        pygame.draw.rect(pantalla, C_PANEL_BORDE,
                         pygame.Rect(PL_X - 4, 70, PL_W + 14, 500), width=2, border_radius=8)

        # -- OPCIÓN 1: Elegir coordenadas de ataque --
        dibujar_texto("OPCION 1: ATACAR AL RIVAL", fuente_seccion, C_AMARILLO,
                      PL_X + 4, 78)

        # Tarjeta del objetivo actual (casilla seleccionada en el radar)
        caja_obj = pygame.Rect(PL_X + 4, 96, PL_W - 8, 30)
        pygame.draw.rect(pantalla, C_PANEL_CLARO, caja_obj, border_radius=5)
        pygame.draw.rect(pantalla, C_MIRA, caja_obj, width=2, border_radius=5)
        est_sel = partida.ataques.estado(dis_f, dis_c)
        est_txt = {0: "Desconocido", 1: "Agua", 2: "Tocado", 3: "Hundido"}.get(est_sel, "")
        dibujar_texto(f"Objetivo: Fila {dis_f}  Col {dis_c}  ({est_txt})",
                      fuente_normal, C_BLANCO, caja_obj.x + 8, caja_obj.y + 7)

        # Texto guía resultado
        dibujar_texto("Resultado que te dice el rival:",
                      fuente_pequena, C_GRIS_CLARO, PL_X + 4, 132)

        # Botones de resultado
        dibujar_boton(btn_agua,    "1. Agua",    C_AZUL_BOTON, C_AZUL_HOVER,
                      seleccionado=(resultado_sel == RES_AGUA))
        dibujar_boton(btn_tocado,  "2. Tocado",  C_AZUL_BOTON, C_AZUL_HOVER,
                      seleccionado=(resultado_sel == RES_TOCADO))
        dibujar_boton(btn_hundido, "3. Hundido", C_AZUL_BOTON, C_AZUL_HOVER,
                      seleccionado=(resultado_sel == RES_HUNDIDO))

        # Botón confirmar disparo
        if resultado_sel == RES_HUNDIDO:
            txt_conf = "Marcar casilla como HUNDIDO"
            c_conf   = C_ROJO_BOTON
            c_conf_h = C_ROJO_HOVER
        else:
            txt_conf = f"Confirmar Disparo  ({resultado_sel.capitalize()})"
            c_conf   = C_VERDE_BOTON
            c_conf_h = C_VERDE_HOVER

        dibujar_boton(btn_confirmar, txt_conf, c_conf, c_conf_h,
                      activo=(partida.turno == TURNO_YO and not partida.terminada))

        # Botón pasar turno
        dibujar_boton(btn_pasar, "Finalizar Turno  (Pasar al Rival)",
                      C_AZUL_BOTON, C_AZUL_HOVER,
                      activo=(partida.turno == TURNO_YO and not partida.terminada))

        # Separador
        pygame.draw.line(pantalla, C_PANEL_BORDE, (PL_X, 285), (ANCHO - 10, 285), 1)

        # -- OPCIÓN 2: Ataque recibido --
        dibujar_texto("OPCION 2: ATAQUE RECIBIDO", fuente_seccion, C_ROJO_HOVER,
                      PL_X + 4, 292)

        caja_rec = pygame.Rect(PL_X + 4, 310, PL_W - 8, 26)
        pygame.draw.rect(pantalla, C_PANEL_CLARO, caja_rec, border_radius=5)
        pygame.draw.rect(pantalla, C_ROJO_HOVER, caja_rec, width=1, border_radius=5)
        dibujar_texto(f"Casilla del rival: Fila {rec_f}  Col {rec_c}",
                      fuente_normal, C_BLANCO, caja_rec.x + 8, caja_rec.y + 5)

        dibujar_boton(btn_calcular, "Calcular Resultado",
                      C_ROJO_BOTON, C_ROJO_HOVER,
                      activo=(partida.turno == TURNO_RIVAL and not partida.terminada))

        # Separador
        pygame.draw.line(pantalla, C_PANEL_BORDE, (PL_X, 388), (ANCHO - 10, 388), 1)

        # -- OPCIÓN 3/4: Radar, Deshacer, Guardar, Salir --
        txt_radar = "Radar IA: ON  (haz clic para desactivar)" if radar_activo \
                    else "Radar IA: OFF  (pistas de disparo)"
        dibujar_boton(btn_radar, txt_radar, C_AZUL_BOTON, C_AZUL_HOVER)
        dibujar_boton(btn_deshacer, "Deshacer", C_AZUL_BOTON, C_AZUL_HOVER,
                      activo=bool(partida._deshacer and not partida.terminada))
        dibujar_boton(btn_guardar,  "Guardar JSON", C_VERDE_BOTON, C_VERDE_HOVER)
        dibujar_boton(btn_salir_menu, "Salir al Menu", C_ROJO_BOTON, C_ROJO_HOVER)

        # -- Mensaje de notificación --
        pygame.draw.line(pantalla, C_PANEL_BORDE, (PL_X, 538), (ANCHO - 10, 538), 1)
        # Dividir el mensaje en líneas de máximo 50 caracteres
        lineas_msg = []
        palabras = msg.split()
        linea_actual = ""
        for p in palabras:
            if len(linea_actual) + len(p) + 1 <= 52:
                linea_actual += (" " if linea_actual else "") + p
            else:
                if linea_actual:
                    lineas_msg.append(linea_actual)
                linea_actual = p
        if linea_actual:
            lineas_msg.append(linea_actual)
        for i, lin in enumerate(lineas_msg[:3]):
            dibujar_texto(lin, fuente_pequena, msg_color, PL_X + 4, 544 + i * 16)

        # ==============================================================
        # PANEL INFERIOR (estado de flotas e historial)
        # ==============================================================
        panel_bot = pygame.Rect(10, 590, 700, 160)
        pygame.draw.rect(pantalla, C_PANEL, panel_bot, border_radius=8)
        pygame.draw.rect(pantalla, C_PANEL_BORDE, panel_bot, width=2, border_radius=8)

        # -- Estado flota propia --
        dibujar_texto("ESTADO DE TU FLOTA", fuente_seccion, C_BLANCO, 20, 600)
        hundidos_p = sum(1 for b in partida.propio.barcos
                         if len(b["impactos"]) >= b["tamano"])
        total_p = len(partida.propio.barcos)
        dibujar_texto(f"Barcos a flote: {total_p - hundidos_p} / {total_p}",
                      fuente_normal, C_GRIS_CLARO, 20, 620)
        dibujar_texto(f"Barcos hundidos: {hundidos_p}",
                      fuente_normal, C_ROJO_HOVER, 20, 640)
        dibujar_texto("TIP: Hundido no salta turno.",
                      fuente_pequena, C_AMARILLO, 20, 660)
        dibujar_texto("Marca todas las casillas hundidas y pulsa 'Finalizar Turno'.",
                      fuente_pequena, C_AMARILLO, 20, 676)
        dibujar_texto("Agua y Tocado cambian turno automaticamente.",
                      fuente_pequena, C_GRIS, 20, 692)

        # Separador vertical en el panel inferior
        pygame.draw.line(pantalla, C_PANEL_BORDE, (355, 598), (355, 745), 1)

        # -- Flota rival y últimas jugadas --
        dibujar_texto("FLOTA RIVAL / HISTORIAL", fuente_seccion, C_BLANCO, 365, 600)
        restantes = partida.ataques.barcos_restantes()
        dibujar_texto(f"Navios rivales estimados: {restantes}",
                      fuente_normal, C_AMARILLO, 365, 620)

        ultimas = partida.historial[-3:] if partida.historial else []
        if not ultimas:
            dibujar_texto("Sin movimientos aun.", fuente_pequena, C_GRIS, 365, 645)
        else:
            for idx, jug in enumerate(ultimas):
                dibujar_texto(jug.descripcion(), fuente_pequena, C_GRIS_CLARO,
                              365, 642 + idx * 20)

        # ==============================================================
        # MODAL DE FIN DE PARTIDA
        # ==============================================================
        if partida.terminada:
            overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            overlay.fill((10, 15, 25, 210))
            pantalla.blit(overlay, (0, 0))

            caja = pygame.Rect(ANCHO // 2 - 240, ALTO // 2 - 120, 480, 240)
            pygame.draw.rect(pantalla, C_PANEL, caja, border_radius=14)
            c_borde_fin = C_VERDE_HOVER if partida.estado == ESTADO_VICTORIA else C_ROJO_HOVER
            pygame.draw.rect(pantalla, c_borde_fin, caja, width=3, border_radius=14)

            if partida.estado == ESTADO_VICTORIA:
                dibujar_texto("¡VICTORIA NAVAL!", fuente_titulo, C_VERDE_HOVER,
                              ANCHO // 2, ALTO // 2 - 70, centrar=True)
                dibujar_texto(f"Has hundido toda la flota de {partida.nombre_rival}.",
                              fuente_normal, C_BLANCO, ANCHO // 2, ALTO // 2 - 30, centrar=True)
            else:
                dibujar_texto("¡FLOTA DESTRUIDA! (DERROTA)", fuente_titulo, C_ROJO_HOVER,
                              ANCHO // 2, ALTO // 2 - 70, centrar=True)
                dibujar_texto(f"{partida.nombre_rival} ha destruido tu escuadra.",
                              fuente_normal, C_BLANCO, ANCHO // 2, ALTO // 2 - 30, centrar=True)

            btn_rev  = pygame.Rect(ANCHO // 2 - 190, ALTO // 2 + 10, 380, 40)
            btn_menu = pygame.Rect(ANCHO // 2 - 190, ALTO // 2 + 60, 380, 40)
            dibujar_boton(btn_rev,  "Jugar Nueva Batalla", C_VERDE_BOTON, C_VERDE_HOVER)
            dibujar_boton(btn_menu, "Salir al Menu Principal", C_ROJO_BOTON, C_ROJO_HOVER)

        pygame.display.flip()

        # ==============================================================
        # EVENTOS
        # ==============================================================
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                pos = ev.pos

                # -- Botones del modal de fin de partida --
                if partida.terminada:
                    btn_rev  = pygame.Rect(ANCHO // 2 - 190, ALTO // 2 + 10, 380, 40)
                    btn_menu = pygame.Rect(ANCHO // 2 - 190, ALTO // 2 + 60, 380, 40)
                    if btn_rev.collidepoint(pos):
                        pantalla_configuracion()
                        return
                    elif btn_menu.collidepoint(pos):
                        pantalla_menu()
                        return
                    continue

                # -- Clic en el RADAR RIVAL → seleccionar casilla objetivo --
                if (ORX <= pos[0] < ORX + TAMANO * TC and
                        ORY <= pos[1] < ORY + TAMANO * TC):
                    dis_c = (pos[0] - ORX) // TC
                    dis_f = (pos[1] - ORY) // TC
                    # Si la casilla ya está tocada, preseleccionar "Hundido"
                    if partida.ataques.estado(dis_f, dis_c) == TOCADO:
                        resultado_sel = RES_HUNDIDO
                    continue

                # -- Clic en el TABLERO PROPIO → seleccionar casilla de ataque recibido --
                if (OPX <= pos[0] < OPX + TAMANO * TC and
                        OPY <= pos[1] < OPY + TAMANO * TC):
                    rec_c = (pos[0] - OPX) // TC
                    rec_f = (pos[1] - OPY) // TC
                    continue

                # -- Selector de resultado del disparo --
                if btn_agua.collidepoint(pos):
                    resultado_sel = RES_AGUA
                elif btn_tocado.collidepoint(pos):
                    resultado_sel = RES_TOCADO
                elif btn_hundido.collidepoint(pos):
                    resultado_sel = RES_HUNDIDO

                # -- OPCIÓN 1: Confirmar disparo --
                elif btn_confirmar.collidepoint(pos) and partida.turno == TURNO_YO:
                    try:
                        partida.disparar(dis_f, dis_c, resultado_sel)
                        if resultado_sel == RES_HUNDIDO:
                            sonar(snd_barco)
                            msg = (f"¡HUNDIDO en ({dis_f},{dis_c})! "
                                   "Marca mas casillas o pulsa 'Finalizar Turno'.")
                            msg_color = C_AMARILLO
                        else:
                            msg = (f"Disparo en ({dis_f},{dis_c}) registrado "
                                   f"como {resultado_sel.upper()}. Turno del rival.")
                            msg_color = C_VERDE_HOVER

                        # Actualizar sugerencia del radar IA
                        if radar_activo and not partida.terminada:
                            try:
                                info_radar = partida.sugerir_pista()
                                casilla_sug = info_radar["casilla"]
                            except Exception:
                                casilla_sug = None
                    except (JuegoError, ValueError) as err:
                        msg = str(err)
                        msg_color = C_ROJO_HOVER

                # -- Pasar turno manualmente (tras marcar todos los hundidos) --
                elif btn_pasar.collidepoint(pos) and partida.turno == TURNO_YO:
                    try:
                        partida.pasar_turno()
                        msg = f"Turno finalizado. Ahora ataca {partida.nombre_rival} (Opcion 2)."
                        msg_color = C_ROJO_HOVER
                    except Exception as err:
                        msg = str(err)
                        msg_color = C_ROJO_HOVER

                # -- OPCIÓN 2: Calcular ataque recibido --
                elif btn_calcular.collidepoint(pos) and partida.turno == TURNO_RIVAL:
                    try:
                        res = partida.recibir_ataque(rec_f, rec_c)
                        if res == RES_HUNDIDO:
                            sonar(snd_barco)
                        msg = (f"Ataque en ({rec_f},{rec_c}): ¡{res.upper()}! "
                               "Comunicaselo a tu rival.")
                        msg_color = (C_AMARILLO if res != RES_AGUA else C_AZUL_IMPACTO)
                    except (JuegoError, ValueError) as err:
                        msg = str(err)
                        msg_color = C_ROJO_HOVER

                # -- Radar IA --
                elif btn_radar.collidepoint(pos):
                    radar_activo = not radar_activo
                    if radar_activo and not partida.terminada:
                        try:
                            info_radar = partida.sugerir_pista()
                            casilla_sug = info_radar["casilla"]
                            dis_f, dis_c = casilla_sug
                            msg = (f"Radar IA ({info_radar['modo'].upper()}): "
                                   f"Casilla sugerida ({dis_f},{dis_c}).")
                            msg_color = C_VERDE_HOVER
                        except Exception as err:
                            msg = f"Radar IA: {err}"
                            casilla_sug = None
                    else:
                        casilla_sug = None
                        info_radar = None

                # -- Deshacer --
                elif btn_deshacer.collidepoint(pos) and partida._deshacer:
                    jug_des = partida.deshacer()
                    if jug_des:
                        msg = f"Deshecha jugada #{jug_des.numero}."
                        msg_color = C_AMARILLO
                        if radar_activo:
                            try:
                                info_radar = partida.sugerir_pista()
                                casilla_sug = info_radar["casilla"]
                            except Exception:
                                pass

                # -- Guardar JSON --
                elif btn_guardar.collidepoint(pos):
                    try:
                        partida.guardar_en_fichero(ARCHIVO_GUARDADO)
                        msg = f"Partida guardada en '{ARCHIVO_GUARDADO}'."
                        msg_color = C_VERDE_HOVER
                    except Exception as err:
                        msg = f"Error al guardar: {err}"
                        msg_color = C_ROJO_HOVER

                # -- Salir al menú --
                elif btn_salir_menu.collidepoint(pos):
                    pantalla_menu()
                    return

        reloj.tick(60)


# -----------------------------------------------------------------------------
# 10. PUNTO DE ENTRADA
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    pantalla_menu()
