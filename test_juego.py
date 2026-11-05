"""
test_juego.py
-------------
Tests unitarios para verificar que toda la lógica del juego funciona bien.

Comprueba:
- Que la flota se genera correctamente (10 barcos, sin solapes ni diagonales).
- Que los ataques devuelven agua/tocado/hundido según corresponda.
- Que el tablero de ataques registra disparos sin propagación automática.
- Que el radar IA sugiere casillas válidas.
- Que el controlador de partida gestiona turnos, deshacer y guardado JSON.

Ejecutar con: python -m unittest test_juego.py

DAM2 - Acceso a Datos - CES Juan Pablo II.
"""

import os
import unittest
from constantes import (
    TAMANO,
    CONFIGURACION_FLOTA,
    RES_AGUA,
    RES_TOCADO,
    RES_HUNDIDO,
    TURNO_YO,
    TURNO_RIVAL,
    ESTADO_VICTORIA,
    ESTADO_DERROTA,
)
from flota import Flota
from ataques import TableroAtaques
import pistas
from partida import Partida, TurnoIncorrecto, PartidaTerminada


class TestFlota(unittest.TestCase):
    def test_generacion_flota(self):
        f = Flota()
        self.assertEqual(f.tamano, 10)
        # Debe haber exactamente 10 barcos: 1x4 + 2x3 + 3x2 + 4x1 = 10
        self.assertEqual(len(f.barcos), 10)

        # Contar cantidades por tamaño
        conteo = {}
        for b in f.barcos:
            conteo[b["tamano"]] = conteo.get(b["tamano"], 0) + 1
        self.assertEqual(conteo, CONFIGURACION_FLOTA)

    def test_matriz_valores(self):
        f = Flota()
        # La matriz debe ser de 10x10 y solo contener 0, 1, 2, 3, 4
        self.assertEqual(len(f.tablero), 10)
        self.assertEqual(len(f.tablero[0]), 10)
        for fila in f.tablero:
            for celda in fila:
                self.assertIn(celda, (0, 1, 2, 3, 4))

    def test_sin_solapes_ni_diagonales(self):
        f = Flota()
        todas_las_celdas = []
        for b in f.barcos:
            for c in b["coordenadas"]:
                self.assertNotIn(c, todas_las_celdas, "Hay casillas solapadas")
                todas_las_celdas.append(c)

    def test_recibir_ataque(self):
        f = Flota()
        # Encontrar una casilla con barco y una de agua
        casilla_barco = f.barcos[0]["coordenadas"][0]
        # Casilla de agua
        casilla_agua = None
        for r in range(10):
            for c in range(10):
                if f.tablero[r][c] == 0:
                    casilla_agua = (r, c)
                    break
            if casilla_agua:
                break

        res_agua = f.recibir_ataque(*casilla_agua)
        self.assertEqual(res_agua, RES_AGUA)

        res_barco = f.recibir_ataque(*casilla_barco)
        self.assertIn(res_barco, (RES_TOCADO, RES_HUNDIDO))


class TestAtaques(unittest.TestCase):
    def test_registro_disparos(self):
        t = TableroAtaques()
        t.registrar_disparo(1, 1, RES_AGUA)
        self.assertEqual(t.estado(1, 1), 1)

        t.registrar_disparo(3, 3, RES_TOCADO)
        self.assertEqual(t.estado(3, 3), 2)

        # Regla estricta: NO hay propagación automática. Cada casilla se marca individualmente
        cambiadas = t.registrar_disparo(3, 4, RES_HUNDIDO)
        self.assertEqual(cambiadas, [(3, 4)])
        self.assertEqual(t.estado(3, 4), 3)
        self.assertEqual(t.estado(3, 3), 2)  # (3, 3) sigue en TOCADO hasta que el usuario la marque

        # El usuario marca (3, 3) como HUNDIDO
        t.registrar_disparo(3, 3, RES_HUNDIDO)
        self.assertEqual(t.estado(3, 3), 3)
        self.assertIn(2, t.hundidos)


class TestPistasIA(unittest.TestCase):
    def test_sugerencia_casilla(self):
        t = TableroAtaques()
        p = pistas.pista(t)
        self.assertIn(p["modo"], ("caza", "objetivo"))
        f, c = p["casilla"]
        self.assertTrue(0 <= f < 10 and 0 <= c < 10)
        self.assertEqual(t.estado(f, c), 0)


class TestPartida(unittest.TestCase):
    def test_flujo_turnos(self):
        p = Partida(empiezo_yo=True)
        self.assertEqual(p.turno, TURNO_YO)

        # Si el rival ataca en mi turno, debe lanzar error
        with self.assertRaises(TurnoIncorrecto):
            p.recibir_ataque(0, 0)

        # 1. Disparo AGUA -> Salta turno al rival
        p.disparar(0, 0, RES_AGUA)
        self.assertEqual(p.turno, TURNO_RIVAL)

        # El rival me ataca a mí -> Vuelve a ser mi turno
        p.recibir_ataque(5, 5)
        self.assertEqual(p.turno, TURNO_YO)

        # 2. Disparo TOCADO -> Salta turno al rival
        p.disparar(1, 1, RES_TOCADO)
        self.assertEqual(p.turno, TURNO_RIVAL)

        # Rival ataca -> Vuelve a ser mi turno
        p.recibir_ataque(6, 6)
        self.assertEqual(p.turno, TURNO_YO)

        # 3. Disparo HUNDIDO -> NO salta turno (permite marcar varias casillas de un barco hundido)
        p.disparar(1, 2, RES_HUNDIDO)
        self.assertEqual(p.turno, TURNO_YO, "Hundido no debe saltar turno")

        # Podemos marcar otra casilla como hundida en la misma ronda sin perder turno
        p.disparar(1, 1, RES_HUNDIDO)
        self.assertEqual(p.turno, TURNO_YO, "Marcar otra casilla hundida no debe saltar turno")

        # Pasamos el turno manualmente cuando terminamos de marcar
        p.pasar_turno()
        self.assertEqual(p.turno, TURNO_RIVAL)

    def test_deshacer(self):
        p = Partida(empiezo_yo=True)
        p.disparar(0, 0, RES_AGUA)
        self.assertEqual(p.turno, TURNO_RIVAL)
        self.assertEqual(len(p.historial), 1)

        p.deshacer()
        self.assertEqual(p.turno, TURNO_YO)
        self.assertEqual(len(p.historial), 0)
        self.assertEqual(p.ataques.estado(0, 0), 0)

    def test_guardar_y_cargar_json(self):
        archivo_temp = "partida_test.json"
        p = Partida(nombre_jugador="Ash", nombre_rival="Gary")
        p.disparar(2, 2, RES_TOCADO)
        p.recibir_ataque(0, 0)
        p.guardar_en_fichero(archivo_temp)

        try:
            p_cargada = Partida.cargar_de_fichero(archivo_temp)
            self.assertEqual(p_cargada.nombre_jugador, "Ash")
            self.assertEqual(p_cargada.nombre_rival, "Gary")
            self.assertEqual(p_cargada.turno, p.turno)
            self.assertEqual(len(p_cargada.historial), 2)
            self.assertEqual(p_cargada.ataques.estado(2, 2), 2)
        finally:
            if os.path.exists(archivo_temp):
                os.remove(archivo_temp)


if __name__ == "__main__":
    unittest.main()
