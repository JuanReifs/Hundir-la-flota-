"""Pruebas de la parte del Integrante 3. Ejecutar: python -m unittest -v"""
import json
import random
import unittest

import pistas
from ataques import TableroAtaques
from constantes import *
from partida import Partida, PartidaTerminada, TurnoIncorrecto, TURNO_RIVAL, TURNO_YO


class TableroPropioFalso:
    """Imita lo que ofrecerá el Integrante 1."""
    def __init__(self, barcos):
        self.barcos = [set(b) for b in barcos]
        self.tocadas = set()

    def recibir_ataque(self, f, c):
        self.tocadas.add((f, c))
        for b in self.barcos:
            if (f, c) in b:
                return RES_HUNDIDO if b <= self.tocadas else RES_TOCADO
        return RES_AGUA

    def todos_hundidos(self):
        return all(b <= self.tocadas for b in self.barcos)


class TestAtaques(unittest.TestCase):
    def test_hundido_marca_todo_el_barco(self):
        t = TableroAtaques()
        t.registrar_disparo(2, 2, RES_TOCADO)
        t.registrar_disparo(2, 3, RES_TOCADO)
        cambiadas = t.registrar_disparo(2, 4, RES_HUNDIDO)
        self.assertEqual(cambiadas, [(2, 2), (2, 3), (2, 4)])
        self.assertTrue(all(t.estado(2, c) == HUNDIDO for c in (2, 3, 4)))
        self.assertEqual(t.hundidos, [3])
        self.assertEqual(t.barcos_restantes(), [4, 3, 2, 2, 2, 1, 1, 1, 1])

    def test_errores_no_modifican_nada(self):
        t = TableroAtaques()
        t.registrar_disparo(0, 0, RES_AGUA)
        with self.assertRaises(ValueError):
            t.registrar_disparo(0, 0, RES_AGUA)
        with self.assertRaises(ValueError):
            t.registrar_disparo(10, 0, RES_AGUA)
        with self.assertRaises(ValueError):
            t.registrar_disparo(1, 1, "nose")
        self.assertEqual(t.estado(1, 1), DESCONOCIDO)

    def test_victoria(self):
        t = TableroAtaques(flota={1: 2})
        t.registrar_disparo(0, 0, RES_HUNDIDO)
        self.assertFalse(t.todos_hundidos())
        t.registrar_disparo(5, 5, RES_HUNDIDO)
        self.assertTrue(t.todos_hundidos())

    def test_bloqueadas(self):
        t = TableroAtaques()
        t.registrar_disparo(0, 0, RES_HUNDIDO)
        self.assertEqual(t.casillas_bloqueadas(), {(0, 1), (1, 0), (1, 1)})
        self.assertEqual(TableroAtaques(barcos_pueden_tocarse=True).casillas_bloqueadas(), set())

    def test_dict(self):
        t = TableroAtaques()
        t.registrar_disparo(3, 3, RES_TOCADO)
        t2 = TableroAtaques.desde_dict(json.loads(json.dumps(t.a_dict())))
        self.assertEqual(t2.casillas, t.casillas)
        self.assertEqual(t2.flota, t.flota)


class TestPistas(unittest.TestCase):
    def test_caza(self):
        t = TableroAtaques()
        p = pistas.pista(t, rng=random.Random(1))
        self.assertEqual(p["modo"], "caza")
        self.assertEqual(t.estado(*p["casilla"]), DESCONOCIDO)

    def test_objetivo_prolonga_linea(self):
        t = TableroAtaques()
        t.registrar_disparo(5, 5, RES_TOCADO)
        t.registrar_disparo(5, 6, RES_TOCADO)
        p = pistas.pista(t)
        self.assertEqual(p["modo"], "objetivo")
        self.assertIn(p["casilla"], [(5, 4), (5, 7)])

    def test_un_tocado_sugiere_adyacente(self):
        t = TableroAtaques()
        t.registrar_disparo(5, 5, RES_TOCADO)
        f, c = pistas.sugerir_casilla(t)
        self.assertEqual(abs(f - 5) + abs(c - 5), 1)

    def test_no_sugiere_alrededor_de_hundido(self):
        t = TableroAtaques()
        t.registrar_disparo(0, 0, RES_HUNDIDO)
        mapa = pistas.mapa_probabilidades(t)
        self.assertEqual((mapa[0][1], mapa[1][0], mapa[1][1]), (0, 0, 0))

    def test_tablero_lleno(self):
        t = TableroAtaques(tamano=2, flota={1: 1})
        for f in range(2):
            for c in range(2):
                t.registrar_disparo(f, c, RES_AGUA)
        with self.assertRaises(ValueError):
            pistas.sugerir_casilla(t)


class TestPartida(unittest.TestCase):
    def test_turnos_y_deshacer(self):
        p = Partida(TableroPropioFalso([[(0, 0)], [(9, 9), (9, 8)]]))
        p.disparar(1, 1, RES_AGUA)
        self.assertEqual(p.turno, TURNO_RIVAL)
        with self.assertRaises(TurnoIncorrecto):
            p.disparar(2, 2, RES_AGUA)
        self.assertEqual(p.recibir_ataque(9, 9), RES_TOCADO)
        self.assertEqual(p.turno, TURNO_YO)
        p.disparar(2, 2, RES_AGUA)
        with self.assertRaises(ValueError):   # el rival no puede repetir casilla
            p.recibir_ataque(9, 9)
        # deshacer de verdad
        p2 = Partida(TableroPropioFalso([[(0, 0)]]))
        p2.disparar(1, 1, RES_AGUA)
        p2.recibir_ataque(0, 0)
        p2.deshacer()
        self.assertEqual(p2.turno, TURNO_RIVAL)
        self.assertNotIn((0, 0), p2.propio.tocadas)
        self.assertEqual(len(p2.historial), 1)
        self.assertEqual(p2.estado, Partida.EN_CURSO)

    def test_derrota(self):
        p = Partida(TableroPropioFalso([[(0, 0)]]), empiezo_yo=False)
        self.assertEqual(p.recibir_ataque(0, 0), RES_HUNDIDO)
        self.assertEqual(p.estado, Partida.DERROTA)
        with self.assertRaises(PartidaTerminada):
            p.disparar(1, 1, RES_AGUA)

    def test_victoria(self):
        p = Partida(TableroPropioFalso([[(0, 0)]]), flota={1: 1})
        p.disparar(4, 4, RES_HUNDIDO)
        self.assertEqual(p.estado, Partida.VICTORIA)

    def test_repite_si_acierta(self):
        p = Partida(TableroPropioFalso([[(0, 0)]]), repite_si_acierta=True)
        p.disparar(4, 4, RES_TOCADO)
        self.assertEqual(p.turno, TURNO_YO)
        p.disparar(4, 5, RES_AGUA)
        self.assertEqual(p.turno, TURNO_RIVAL)

    def test_guardar_y_cargar(self):
        p = Partida(TableroPropioFalso([[(0, 0)]]))
        p.disparar(4, 4, RES_TOCADO)
        p.recibir_ataque(7, 7)
        datos = json.loads(json.dumps(p.a_dict()))
        q = Partida.desde_dict(datos, p.propio)
        self.assertEqual(q.ataques.casillas, p.ataques.casillas)
        self.assertEqual(q.recibidos, p.recibidos)
        self.assertEqual([j.descripcion() for j in q.historial],
                         [j.descripcion() for j in p.historial])

    def test_coordenadas_texto(self):
        self.assertEqual(texto_a_coord("b3"), (2, 1))
        self.assertEqual(coord_a_texto(2, 1), "B3")
        for malo in ("K1", "A0", "A11", "", "3B"):
            with self.assertRaises(ValueError):
                texto_a_coord(malo)


if __name__ == "__main__":
    unittest.main()
