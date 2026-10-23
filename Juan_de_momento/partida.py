"""INTEGRANTE 3: controlador de la partida.

Es lo único que necesita conocer la interfaz (Integrante 2). Une:
  - tu tablero (Integrante 1): `tablero_propio`, con recibir_ataque() y todos_hundidos()
  - el tablero de ataques (ataques.py)
  - las pistas (pistas.py)

Flujo de juego (los dos jugadores están en ordenadores distintos):
  - Tu turno:    disparar(fila, col, resultado_que_te_dice_el_rival)
  - Turno rival: recibir_ataque(fila, col) -> el programa calcula y devuelve
                 "agua" / "tocado" / "hundido" para que se lo digas al rival.

NOTA para el Integrante 1: el deshacer guarda copias de `tablero_propio.__dict__`,
así que la clase debe ser una clase normal (sin __slots__).
"""

import copy
from dataclasses import dataclass, asdict

import pistas
from ataques import TableroAtaques
from constantes import TAMANO, RES_AGUA, coord_a_texto

TURNO_YO = "yo"
TURNO_RIVAL = "rival"


class JuegoError(ValueError):
    pass


class PartidaTerminada(JuegoError):
    pass


class TurnoIncorrecto(JuegoError):
    pass


@dataclass
class Jugada:
    numero: int
    tipo: str          # "disparo" (tuyo) o "recibido" (del rival)
    fila: int
    col: int
    resultado: str

    def descripcion(self):
        casilla = coord_a_texto(self.fila, self.col)
        if self.tipo == "disparo":
            return f"#{self.numero} Disparas a {casilla}: {self.resultado}"
        return f"#{self.numero} El rival dispara a {casilla}: {self.resultado}"


class Partida:
    EN_CURSO = "en_curso"
    VICTORIA = "victoria"
    DERROTA = "derrota"

    def __init__(self, tablero_propio, tamano=TAMANO, flota=None,
                 barcos_pueden_tocarse=False, empiezo_yo=True,
                 repite_si_acierta=False, forzar_turnos=True):
        self.propio = tablero_propio
        self.ataques = TableroAtaques(tamano, flota, barcos_pueden_tocarse)
        self.turno = TURNO_YO if empiezo_yo else TURNO_RIVAL
        self.repite_si_acierta = repite_si_acierta  # ¿repite turno quien toca?
        self.forzar_turnos = forzar_turnos
        self.historial = []
        self.recibidos = set()   # casillas que el rival ya ha atacado
        self._deshacer = []      # fotos para deshacer (no se guardan en disco)

    # ---------- estado ----------
    @property
    def estado(self):
        if self.ataques.todos_hundidos():
            return self.VICTORIA
        if self.propio.todos_hundidos():
            return self.DERROTA
        return self.EN_CURSO

    @property
    def terminada(self):
        return self.estado != self.EN_CURSO

    def resumen(self):
        return {
            "estado": self.estado,
            "turno": self.turno,
            "barcos_enemigos_restantes": self.ataques.barcos_restantes(),
            "barcos_enemigos_hundidos": len(self.ataques.hundidos),
            "jugadas": len(self.historial),
            "se_puede_deshacer": bool(self._deshacer),
        }

    # ---------- acciones ----------
    def disparar(self, fila, col, resultado):
        """Opción 1: marcas tu disparo con el resultado que te dijo el rival.
        Devuelve las casillas cambiadas (para repintar)."""
        self._comprobar(TURNO_YO)
        foto = self._foto()
        casillas = self.ataques.registrar_disparo(fila, col, resultado)  # puede lanzar ValueError
        self._anotar(foto, "disparo", fila, col, resultado)
        self._cambiar_turno(resultado)
        return casillas

    def recibir_ataque(self, fila, col):
        """Opción 2: el rival dispara a (fila, col). Devuelve "agua"/"tocado"/"hundido"."""
        self._comprobar(TURNO_RIVAL)
        if not self.ataques.dentro(fila, col):
            raise ValueError(f"Coordenadas fuera del tablero: ({fila}, {col})")
        if (fila, col) in self.recibidos:
            raise ValueError("El rival ya había atacado esa casilla")
        foto = self._foto()
        resultado = self.propio.recibir_ataque(fila, col)
        self.recibidos.add((fila, col))
        self._anotar(foto, "recibido", fila, col, resultado)
        self._cambiar_turno(resultado)
        return resultado

    def sugerir(self):
        """Pista completa (ver pistas.pista)."""
        return pistas.pista(self.ataques)

    def sugerir_casilla(self):
        return pistas.sugerir_casilla(self.ataques)

    def deshacer(self):
        """Deshace la última jugada. Devuelve la Jugada deshecha o None si no hay."""
        if not self._deshacer:
            return None
        foto = self._deshacer.pop()
        self._restaurar(self.propio, foto["propio"])
        self._restaurar(self.ataques, foto["ataques"])
        self.turno = foto["turno"]
        self.recibidos = foto["recibidos"]
        return self.historial.pop()

    # ---------- internos ----------
    def _comprobar(self, quien):
        if self.terminada:
            raise PartidaTerminada("La partida ya ha terminado")
        if self.forzar_turnos and self.turno != quien:
            de_quien = "del rival" if self.turno == TURNO_RIVAL else "tuyo"
            raise TurnoIncorrecto(f"Ahora es el turno {de_quien}")

    def _cambiar_turno(self, resultado):
        if self.repite_si_acierta and resultado != RES_AGUA:
            return
        self.turno = TURNO_RIVAL if self.turno == TURNO_YO else TURNO_YO

    def _foto(self):
        return {
            "propio": copy.deepcopy(self.propio.__dict__),
            "ataques": copy.deepcopy(self.ataques.__dict__),
            "turno": self.turno,
            "recibidos": set(self.recibidos),
        }

    @staticmethod
    def _restaurar(objeto, foto):
        # Se restaura el contenido sin cambiar el objeto, para que la interfaz
        # no pierda sus referencias.
        objeto.__dict__.clear()
        objeto.__dict__.update(foto)

    def _anotar(self, foto, tipo, fila, col, resultado):
        self._deshacer.append(foto)
        self.historial.append(Jugada(len(self.historial) + 1, tipo, fila, col, resultado))

    # ---------- guardado (el tablero propio lo guarda persistencia.py) ----------
    def a_dict(self):
        return {
            "ataques": self.ataques.a_dict(),
            "turno": self.turno,
            "repite_si_acierta": self.repite_si_acierta,
            "forzar_turnos": self.forzar_turnos,
            "recibidos": sorted(self.recibidos),
            "historial": [asdict(j) for j in self.historial],
        }

    @classmethod
    def desde_dict(cls, datos, tablero_propio):
        a = datos["ataques"]
        p = cls(tablero_propio, a["tamano"], {int(k): v for k, v in a["flota"].items()},
                a["barcos_pueden_tocarse"], repite_si_acierta=datos["repite_si_acierta"],
                forzar_turnos=datos["forzar_turnos"])
        p.ataques = TableroAtaques.desde_dict(a)
        p.turno = datos["turno"]
        p.recibidos = {tuple(x) for x in datos["recibidos"]}
        p.historial = [Jugada(**j) for j in datos["historial"]]
        return p  # tras cargar no se puede deshacer lo anterior
