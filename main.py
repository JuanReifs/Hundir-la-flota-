import sys
import subprocess

try:
    import pygame
    print("Ya lo tienes instalado")
except ImportError:
    print("Instalando las dependencias del juego...")

    subprocess.check_call([sys.executable, "-m","pip","install","pygame"])

    import pygame

pygame.init()

ancho = 1000
alto = 650

pantalla = pygame.display.set_mode((ancho,alto))

# Cargar la imagen de fondo
fondo = pygame.image.load("Imagenes/Imagen_inicio.png")

# Adaptarla al tamaño de la ventana
fondo = pygame.transform.scale(
    fondo, (ancho, alto)
)

pantalla.fill(fondo)



print("Listo rey")