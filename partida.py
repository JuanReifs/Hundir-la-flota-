"""
partida.py
----------
Controlador principal de la partida: une todos los módulos del juego.

Se encarga de:
- Coordinar el tablero propio (flota.py) con el de ataques (ataques.py).
- Gestionar los turnos (quién dispara y quién recibe).
- Implementar las 4 opciones del menú: atacar, recibir, visualizar, salir.
- Guardar y cargar la partida completa en formato JSON (Acceso a Datos).
- Conectar con el radar IA (pistas.py) para sugerir casillas.

Reglas de turno:
- HUNDIDO no cambia de turno (el jugador puede marcar varias casillas seguidas).
- AGUA y TOCADO cambian de turno automáticamente.
- El jugador pulsa "Pasar turno" manualmente cuando termina de marcar hundidos.

DAM2 - Acceso a Datos - CES Juan Pablo II.
"""

import copy
import json
from dataclasses import dataclass, asdict

import pistas
from ataques import TableroAtaques
from constantes import (
    TAMANO,
    CONFIGURACION_FLOTA,
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


class JuegoError(Exception):
    """Excepción base para errores de lógica de juego."""
    pass


class PartidaTerminada(JuegoError):
    """Se intenta realizar una jugada cuando la partida ya ha concluido."""
    pass


class TurnoIncorrecto(JuegoError):
    """Se intenta jugar en el turno del contrincante."""
    pass


@dataclass
class Jugada:
    """Representa una acción individual en el historial de la partida."""
    numero: int
    tipo: str  # "disparo" (nuestro) o "recibido" (del rival)
    fila: int
    col: int
    resultado: str

    def descripcion(self):
        casilla = coord_a_texto(self.fila, self.col)
        if self.tipo == "disparo":
            return f"#{self.numero} Has disparado a {casilla} -> {self.resultado.upper()}"
        return f"#{self.numero} Rival dispara a {casilla} -> {self.resultado.upper()}"


class Partida:
    """Controlador que sincroniza ambos tableros, gestiona los turnos y la persistencia."""

    EN_CURSO = ESTADO_EN_CURSO
    VICTORIA = ESTADO_VICTORIA
    DERROTA = ESTADO_DERROTA

    def __init__(
        self,
        tablero_propio=None,
        nombre_jugador="Jugador",
        nombre_rival="Rival",
        tamano=TAMANO,
        flota=None,
        barcos_pueden_tocarse=False,
        empiezo_yo=True,
        repite_si_acierta=False,
        forzar_turnos=True,
    ):
        self.nombre_jugador = nombre_jugador
        self.nombre_rival = nombre_rival
        self.tamano = tamano
        self.flota_config = dict(flota if flota is not None else CONFIGURACION_FLOTA)

        # Tablero propio (nuestra flota)
        if tablero_propio is not None:
            self.propio = tablero_propio
        else:
            self.propio = Flota(tamano=self.tamano, configuracion=self.flota_config)

        # Tablero de ataques (nuestros disparos al rival)
        self.ataques = TableroAtaques(
            tamano=self.tamano,
            flota=self.flota_config,
            barcos_pueden_tocarse=barcos_pueden_tocarse,
        )

        self.turno = TURNO_YO if empiezo_yo else TURNO_RIVAL
        self.repite_si_acierta = repite_si_acierta
        self.forzar_turnos = forzar_turnos
        self.historial = []
        self.recibidos = set()
        self._deshacer = []

    @property
    def estado(self):
        """Calcula el estado actual de la partida (victoria, derrota o en curso)."""
        if self.ataques.todos_hundidos():
            return self.VICTORIA
        if self.propio.todos_hundidos():
            return self.DERROTA
        return self.EN_CURSO

    @property
    def terminada(self):
        return self.estado != self.EN_CURSO

    def disparar(self, fila, col, resultado):
        """
        OPCIÓN 1 DEL MENÚ:
        Registra el resultado (agua, tocado o hundido) que el rival nos ha comunicado.
        REGLA DE TURNOS:
        - Si es 'agua' o 'tocado': cambia el turno automáticamente al rival.
        - Si es 'hundido': NO cambia de turno, permitiendo marcar todas las casillas
          necesarias del barco hundido sin saltar ronda ni perder turnos.
        """
        self._comprobar_turno(TURNO_YO)
        foto = self._guardar_foto()

        # Registrar en el tablero de ataques (casilla individual sin propagación)
        casillas_modificadas = self.ataques.registrar_disparo(fila, col, resultado)

        # Anotar en el historial
        self._anotar(foto, "disparo", fila, col, resultado)

        # Hundido NO salta turno; agua y tocado sí
        if resultado != RES_HUNDIDO:
            self._cambiar_turno(resultado)

        return casillas_modificadas

    def pasar_turno(self):
        """Pasa manualmente el turno al rival tras marcar las casillas del barco hundido."""
        self._comprobar_turno(TURNO_YO)
        self.turno = TURNO_RIVAL

    def marcar_casilla_hundida(self, fila, col):
        """Permite convertir individualmente una casilla tocada a hundida sin saltar turno."""
        return self.disparar(fila, col, RES_HUNDIDO)

    def recibir_ataque(self, fila, col):
        """
        OPCIÓN 2 DEL MENÚ:
        Procesa el ataque del rival en nuestra flota y devuelve automáticamente
        el resultado ('agua', 'tocado' o 'hundido') para decírselo al contrincante.
        """
        self._comprobar_turno(TURNO_RIVAL)
        if not (0 <= fila < self.tamano and 0 <= col < self.tamano):
            raise ValueError(f"Coordenadas fuera del tablero: ({fila}, {col})")
        if (fila, col) in self.recibidos:
            raise ValueError(f"El rival ya había atacado la casilla ({fila}, {col})")

        foto = self._guardar_foto()

        # Calcular el impacto en nuestra flota
        resultado = self.propio.recibir_ataque(fila, col)
        self.recibidos.add((fila, col))

        # Anotar en el historial y cambiar el turno
        self._anotar(foto, "recibido", fila, col, resultado)
        self._cambiar_turno(resultado)
        return resultado

    def sugerir_pista(self):
        """Devuelve la recomendación del radar IA para disparar al rival."""
        return pistas.pista(self.ataques)

    def sugerir_casilla(self):
        """Devuelve la mejor casilla (f, c) sugerida por la IA."""
        return pistas.sugerir_casilla(self.ataques)

    def deshacer(self):
        """Deshace la última jugada realizada (útil si hubo error al dictar coordenadas)."""
        if not self._deshacer:
            return None

        foto = self._deshacer.pop()
        self._restaurar(self.propio, foto["propio"])
        self._restaurar(self.ataques, foto["ataques"])
        self.turno = foto["turno"]
        self.recibidos = foto["recibidos"]
        return self.historial.pop() if self.historial else None

    def resumen(self):
        """Resumen rápido del estado de la partida para la interfaz."""
        return {
            "estado": self.estado,
            "turno": self.turno,
            "nombre_jugador": self.nombre_jugador,
            "nombre_rival": self.nombre_rival,
            "barcos_enemigos_restantes": self.ataques.barcos_restantes(),
            "barcos_enemigos_hundidos": len(self.ataques.hundidos),
            "nuestros_barcos_hundidos": sum(
                1 for b in getattr(self.propio, "barcos", []) if len(b["impactos"]) >= b["tamano"]
            ) if hasattr(self.propio, "barcos") else 0,
            "jugadas": len(self.historial),
            "se_puede_deshacer": bool(self._deshacer),
        }

    # Métodos internos
    def _comprobar_turno(self, turno_esperado):
        if self.terminada:
            raise PartidaTerminada("La partida ya ha finalizado.")
        if self.forzar_turnos and self.turno != turno_esperado:
            turno_nombre = "tuyo" if turno_esperado == TURNO_YO else f"del rival"
            raise TurnoIncorrecto(f"Ahora es el turno {turno_nombre}")

    def _cambiar_turno(self, resultado):
        if self.repite_si_acierta and resultado != RES_AGUA:
            return
        self.turno = TURNO_RIVAL if self.turno == TURNO_YO else TURNO_YO

    def _guardar_foto(self):
        return {
            "propio": copy.deepcopy(self.propio.__dict__),
            "ataques": copy.deepcopy(self.ataques.__dict__),
            "turno": self.turno,
            "recibidos": set(self.recibidos),
        }

    @staticmethod
    def _restaurar(objeto, estado_guardado):
        objeto.__dict__.clear()
        objeto.__dict__.update(estado_guardado)

    def _anotar(self, foto, tipo, fila, col, resultado):
        self._deshacer.append(foto)
        jugada = Jugada(len(self.historial) + 1, tipo, fila, col, resultado)
        self.historial.append(jugada)

    # ----------------------------------------------------
    # PERSISTENCIA EN FICHERO JSON (Módulo Acceso a Datos)
    # ----------------------------------------------------
    def a_dict(self):
        """Convierte toda la partida a estructura serializable en JSON."""
        datos = {
            "nombre_jugador": self.nombre_jugador,
            "nombre_rival": self.nombre_rival,
            "tamano": self.tamano,
            "turno": self.turno,
            "repite_si_acierta": self.repite_si_acierta,
            "forzar_turnos": self.forzar_turnos,
            "recibidos": sorted(self.recibidos),
            "tablero_ataques": self.ataques.a_dict(),
            "ataques": self.ataques.a_dict(),  # Compatibilidad con Juan_de_momento
            "historial": [asdict(j) for j in self.historial],
        }
        if hasattr(self.propio, "a_dict"):
            datos["tablero_propio"] = self.propio.a_dict()
        return datos

    @classmethod
    def desde_dict(cls, datos, tablero_propio=None):
        """Reconstruye una partida completa desde un diccionario JSON."""
        if tablero_propio is None and "tablero_propio" in datos:
            tablero_propio = Flota.desde_dict(datos["tablero_propio"])

        datos_ataques = datos.get("tablero_ataques") or datos.get("ataques")
        partida = cls(
            tablero_propio=tablero_propio,
            nombre_jugador=datos.get("nombre_jugador", "Jugador"),
            nombre_rival=datos.get("nombre_rival", "Rival"),
            tamano=datos.get("tamano", datos_ataques.get("tamano", TAMANO)),
            repite_si_acierta=datos.get("repite_si_acierta", False),
            forzar_turnos=datos.get("forzar_turnos", True),
        )
        partida.ataques = TableroAtaques.desde_dict(datos_ataques)
        partida.turno = datos.get("turno", TURNO_YO)
        partida.recibidos = {tuple(x) for x in datos.get("recibidos", [])}
        partida.historial = [Jugada(**j) for j in datos.get("historial", [])]
        return partida

    def guardar_en_fichero(self, ruta=ARCHIVO_GUARDADO):
        """Guarda la partida actual en el fichero JSON especificado."""
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(self.a_dict(), f, indent=4, ensure_ascii=False)

    @classmethod
    def cargar_de_fichero(cls, ruta=ARCHIVO_GUARDADO):
        """Carga una partida existente desde un fichero JSON."""
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return cls.desde_dict(datos)
