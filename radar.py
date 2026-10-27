# -*- coding: utf-8 -*-
"""
TOCADO Y HUNDIDO · RADAR IA
===========================
Juego de hundir la flota (10x10) con interfaz gráfica en tkinter.

La "IA" calcula, a partir de los resultados anteriores (agua / tocado / hundido),
en qué casillas es más probable que haya un barco. Al principio de cada ronda
un ESCÁNER barre el tablero enemigo y pinta ese mapa de calor.
La IA rival usa el mismo cerebro para disparar a tu flota (y verás su escáner en rojo).

Ejecutar:  python tocado_hundido.py
"""
import random
import tkinter as tk
from tkinter import messagebox

# ───────────────────────── Configuración ─────────────────────────
TAM = 10
FLOTA = [("Portaaviones", 5), ("Acorazado", 4), ("Crucero", 3),
         ("Submarino", 3), ("Destructor", 2)]

CELDA = 36      # tamaño de cada casilla en píxeles
MARGEN = 26     # espacio para las letras / números

# Estados de una casilla disparada
DESCONOCIDO, AGUA, TOCADO, HUNDIDO = 0, 1, 2, 3

# Colores
C_FONDO = "#06111d"
C_PANEL = "#0b1d30"
C_AGUA = "#0e2a45"
C_GRID = "#16405f"
C_TEXTO = "#cfe8ff"
C_VERDE = "#39ff88"
C_ROJO = "#ff5a4f"
C_BARCO = "#6f8aa6"
C_HUNDIDO = "#5c1616"


# ───────────────────────── Utilidades ─────────────────────────
def mezclar(c1, c2, t):
    """Interpola entre dos colores hexadecimales (t entre 0 y 1)."""
    t = max(0.0, min(1.0, t))
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def color_calor(r, lado):
    """r = probabilidad relativa (0..1). Verde para tu radar, rojo para el de la IA enemiga."""
    r = r ** 0.8
    if lado == "enemigo":
        if r < 0.6:
            return mezclar(C_AGUA, "#1b8f5a", r / 0.6)
        return mezclar("#1b8f5a", "#e6ff4d", (r - 0.6) / 0.4)
    if r < 0.6:
        return mezclar(C_AGUA, "#8f2a2a", r / 0.6)
    return mezclar("#8f2a2a", "#ff8a3d", (r - 0.6) / 0.4)


def coord(pos):
    f, c = pos
    return f"{chr(65 + c)}{f + 1}"


# ───────────────────────── Lógica del juego ─────────────────────────
class Barco:
    def __init__(self, nombre, celdas):
        self.nombre = nombre
        self.celdas = set(celdas)
        self.tocadas = set()

    @property
    def hundido(self):
        return self.tocadas == self.celdas


class Tablero:
    def __init__(self):
        self.barcos = []
        self.ocupadas = set()
        self.disparos = {}          # (fila, col) -> AGUA / TOCADO / HUNDIDO
        self.colocar_aleatorio()

    def colocar_aleatorio(self):
        self.barcos, self.ocupadas, self.disparos = [], set(), {}
        for nombre, largo in FLOTA:
            while True:
                horizontal = random.random() < 0.5
                f = random.randrange(TAM if horizontal else TAM - largo + 1)
                c = random.randrange(TAM - largo + 1 if horizontal else TAM)
                celdas = [(f, c + i) if horizontal else (f + i, c) for i in range(largo)]
                if not any(p in self.ocupadas for p in celdas):
                    self.ocupadas.update(celdas)
                    self.barcos.append(Barco(nombre, celdas))
                    break

    def disparar(self, pos):
        """Devuelve ('agua' | 'tocado' | 'hundido', barco_o_None)."""
        for b in self.barcos:
            if pos in b.celdas:
                b.tocadas.add(pos)
                if b.hundido:
                    for p in b.celdas:
                        self.disparos[p] = HUNDIDO
                    return "hundido", b
                self.disparos[pos] = TOCADO
                return "tocado", b
        self.disparos[pos] = AGUA
        return "agua", None

    def todos_hundidos(self):
        return all(b.hundido for b in self.barcos)

    def longitudes_restantes(self):
        return [len(b.celdas) for b in self.barcos if not b.hundido]


class CerebroIA:
    """
    Calcula un mapa de calor sin conocer dónde están los barcos.

    Idea: probamos TODAS las posiciones posibles de cada barco que sigue a flote.
      - Una posición es válida si no pisa agua ni un barco ya hundido.
      - Cada casilla suma +peso por cada posición válida que la cubre.
      - Si la posición cubre casillas "tocado", su peso se multiplica (modo caza):
        así la IA rodea y remata los barcos que ha tocado.
    """
    PESO_TOCADO = 40

    @staticmethod
    def calcular(disparos, restantes):
        calor = [[0.0] * TAM for _ in range(TAM)]
        for largo in restantes:
            for horizontal in (True, False):
                max_f = TAM if horizontal else TAM - largo + 1
                max_c = TAM - largo + 1 if horizontal else TAM
                for f in range(max_f):
                    for c in range(max_c):
                        celdas = [(f, c + i) if horizontal else (f + i, c) for i in range(largo)]
                        tocadas, valido = 0, True
                        for p in celdas:
                            e = disparos.get(p, DESCONOCIDO)
                            if e == AGUA or e == HUNDIDO:
                                valido = False
                                break
                            if e == TOCADO:
                                tocadas += 1
                        if not valido:
                            continue
                        peso = CerebroIA.PESO_TOCADO ** tocadas
                        for p in celdas:
                            if p not in disparos:
                                calor[p[0]][p[1]] += peso
        return calor

    @staticmethod
    def mejor(calor, disparos):
        libres = [(f, c) for f in range(TAM) for c in range(TAM) if (f, c) not in disparos]
        if not libres:
            return None
        m = max(calor[f][c] for f, c in libres)
        if m <= 0:
            return random.choice(libres)
        return random.choice([p for p in libres if calor[p[0]][p[1]] >= m * 0.999])


# ───────────────────────── Interfaz ─────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tocado y Hundido · Radar IA")
        self.configure(bg=C_FONDO)
        self.resizable(False, False)

        self.gen = 0                    # invalida animaciones de partidas anteriores
        self.fase = 0                   # para el parpadeo de la casilla sugerida
        self.hover = None
        self.var_escaner = tk.BooleanVar(value=True)

        self.construir_ui()
        self.nueva_partida()
        self.pulso()

    # ---------- construcción de la ventana ----------
    def construir_ui(self):
        cab = tk.Frame(self, bg=C_FONDO)
        cab.pack(fill="x", padx=16, pady=(12, 4))
        tk.Label(cab, text="◉ TOCADO Y HUNDIDO · RADAR IA", bg=C_FONDO, fg=C_VERDE,
                 font=("Consolas", 16, "bold")).pack(side="left")
        self.lbl_ronda = tk.Label(cab, text="", bg=C_FONDO, fg=C_TEXTO, font=("Consolas", 12))
        self.lbl_ronda.pack(side="right")

        self.lbl_estado = tk.Label(self, text="", bg=C_FONDO, fg=C_VERDE,
                                   font=("Consolas", 11), anchor="w")
        self.lbl_estado.pack(fill="x", padx=16)

        tableros = tk.Frame(self, bg=C_FONDO)
        tableros.pack(padx=16, pady=8)
        self.cv = {}
        titulos = {"enemigo": "MAR ENEMIGO (haz clic para disparar)", "propio": "TU FLOTA"}
        for i, lado in enumerate(("enemigo", "propio")):
            col = tk.Frame(tableros, bg=C_FONDO)
            col.grid(row=0, column=i, padx=10)
            tk.Label(col, text=titulos[lado], bg=C_FONDO, fg=C_TEXTO,
                     font=("Consolas", 10, "bold")).pack(pady=(0, 4))
            lado_px = MARGEN + TAM * CELDA + 4
            cv = tk.Canvas(col, width=lado_px, height=lado_px, bg=C_PANEL,
                           highlightthickness=1, highlightbackground=C_GRID)
            cv.pack()
            self.cv[lado] = cv
        self.cv["enemigo"].configure(cursor="crosshair")
        self.cv["enemigo"].bind("<Button-1>", self.clic_enemigo)
        self.cv["enemigo"].bind("<Motion>", self.mover)
        self.cv["enemigo"].bind("<Leave>", lambda e: self.quitar_hover())

        inf = tk.Frame(self, bg=C_FONDO)
        inf.pack(fill="x", padx=16, pady=(0, 12))
        self.txt = tk.Text(inf, width=58, height=9, bg=C_PANEL, fg=C_TEXTO, relief="flat",
                           font=("Consolas", 10), state="disabled", wrap="word")
        self.txt.pack(side="left")
        for tag, color in (("info", "#8aa4bd"), ("agua", "#6cc4ff"), ("tocado", "#ffb347"),
                           ("hundido", C_ROJO), ("ia", C_VERDE)):
            self.txt.tag_config(tag, foreground=color)

        der = tk.Frame(inf, bg=C_FONDO)
        der.pack(side="left", fill="both", expand=True, padx=(14, 0))
        estilo = dict(bg=C_GRID, fg=C_TEXTO, activebackground=C_VERDE, activeforeground="#000",
                      relief="flat", font=("Consolas", 10, "bold"), padx=8, pady=4)
        tk.Button(der, text="Nueva partida", command=self.nueva_partida, **estilo).pack(fill="x")
        tk.Button(der, text="Disparar a la sugerencia IA", command=self.disparar_sugerencia,
                  **estilo).pack(fill="x", pady=4)
        tk.Checkbutton(der, text="Escáner IA activado", variable=self.var_escaner,
                       bg=C_FONDO, fg=C_TEXTO, selectcolor=C_PANEL, activebackground=C_FONDO,
                       activeforeground=C_VERDE, font=("Consolas", 10)).pack(anchor="w")
        self.lbl_flota_e = tk.Label(der, bg=C_FONDO, fg=C_TEXTO, justify="left",
                                    font=("Consolas", 9), anchor="w")
        self.lbl_flota_e.pack(fill="x", pady=(6, 0))
        self.lbl_flota_p = tk.Label(der, bg=C_FONDO, fg=C_TEXTO, justify="left",
                                    font=("Consolas", 9), anchor="w")
        self.lbl_flota_p.pack(fill="x", pady=(4, 0))

    # ---------- partida ----------
    def nueva_partida(self):
        self.gen += 1
        self.enemigo = Tablero()
        self.propio = Tablero()
        self.heat = {"enemigo": None, "propio": None}
        self.scan = {"enemigo": None, "propio": None}   # progreso del barrido (0..1) o None
        self.sugerida = None
        self.esperando = False
        self.revelar = False
        self.ronda = 0
        self.tiros = 0
        self.hover = None

        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.configure(state="disabled")
        self.log("Flotas desplegadas. ¡Que empiece la batalla!", "info")

        self.actualizar_panel()
        self.redibujar()
        self.iniciar_ronda()

    def despues(self, ms, fn):
        """after() que se cancela solo si empieza otra partida."""
        gen = self.gen
        self.after(ms, lambda: fn() if gen == self.gen else None)

    def iniciar_ronda(self):
        self.ronda += 1
        self.actualizar_panel()
        if self.var_escaner.get():
            calor = CerebroIA.calcular(self.enemigo.disparos, self.enemigo.longitudes_restantes())
            self.heat["enemigo"] = calor
            self.sugerida = CerebroIA.mejor(calor, self.enemigo.disparos)
            self.estado("Escaneando el mar enemigo...")
            self.lanzar_scan("enemigo", 40, self.fin_scan_jugador)
        else:
            self.esperando = True
            self.estado("Tu turno: elige una casilla.")

    def fin_scan_jugador(self):
        self.esperando = True
        self.log(f"[Ronda {self.ronda}] Escáner completo. Sugerencia IA: {coord(self.sugerida)}", "ia")
        self.estado(f"Tu turno · la IA sugiere {coord(self.sugerida)} (casilla parpadeante)")
        self.redibujar()

    def lanzar_scan(self, lado, frames, al_terminar):
        paso = [0]

        def tick():
            paso[0] += 1
            if paso[0] >= frames:
                self.scan[lado] = None
                self.redibujar()
                al_terminar()
            else:
                self.scan[lado] = paso[0] / frames
                self.redibujar()
                self.despues(28, tick)
        tick()

    # ---------- turnos ----------
    def clic_enemigo(self, ev):
        if not self.esperando:
            return
        pos = self.celda_evento(ev)
        if pos is None or pos in self.enemigo.disparos:
            return
        self.disparo_jugador(pos)

    def disparar_sugerencia(self):
        if not self.esperando:
            return
        pos = self.sugerida
        if pos is None:
            calor = CerebroIA.calcular(self.enemigo.disparos, self.enemigo.longitudes_restantes())
            pos = CerebroIA.mejor(calor, self.enemigo.disparos)
        self.disparo_jugador(pos)

    def disparo_jugador(self, pos):
        self.esperando = False
        self.heat["enemigo"] = None
        self.sugerida = None
        self.tiros += 1
        res, barco = self.enemigo.disparar(pos)
        self.log_resultado("Tú", pos, res, barco)
        self.actualizar_panel()
        self.redibujar()
        if self.enemigo.todos_hundidos():
            self.fin(True)
            return
        self.estado("Turno de la IA enemiga...")
        self.despues(500, self.turno_enemigo)

    def turno_enemigo(self):
        self.heat["propio"] = CerebroIA.calcular(self.propio.disparos,
                                                 self.propio.longitudes_restantes())
        self.lanzar_scan("propio", 24, self.disparo_enemigo)

    def disparo_enemigo(self):
        pos = CerebroIA.mejor(self.heat["propio"], self.propio.disparos)
        res, barco = self.propio.disparar(pos)
        self.log_resultado("IA enemiga", pos, res, barco)
        self.actualizar_panel()
        self.redibujar()
        if self.propio.todos_hundidos():
            self.heat["propio"] = None
            self.redibujar()
            self.fin(False)
            return

        def siguiente():
            self.heat["propio"] = None
            self.redibujar()
            self.iniciar_ronda()
        self.despues(800, siguiente)

    def fin(self, gana):
        self.esperando = False
        self.revelar = not gana
        self.redibujar()
        if gana:
            msg = f"¡VICTORIA! Hundiste toda la flota enemiga en {self.tiros} disparos."
            self.log(msg, "ia")
        else:
            msg = "DERROTA. La IA enemiga hundió toda tu flota."
            self.log(msg, "hundido")
        self.estado(msg)
        if messagebox.askyesno("Fin de la partida", msg + "\n\n¿Jugar otra partida?"):
            self.nueva_partida()

    # ---------- log y paneles ----------
    def log(self, texto, tag="info"):
        self.txt.configure(state="normal")
        self.txt.insert("end", texto + "\n", tag)
        self.txt.see("end")
        self.txt.configure(state="disabled")

    def log_resultado(self, quien, pos, res, barco):
        if res == "agua":
            self.log(f"{quien} dispara a {coord(pos)}: AGUA", "agua")
        elif res == "tocado":
            self.log(f"{quien} dispara a {coord(pos)}: ¡TOCADO!", "tocado")
        else:
            self.log(f"{quien} dispara a {coord(pos)}: ¡HUNDIDO! ({barco.nombre})", "hundido")

    def estado(self, texto):
        self.lbl_estado.configure(text=texto)

    def actualizar_panel(self):
        self.lbl_ronda.configure(text=f"Ronda {self.ronda}")

        def texto(titulo, t):
            lineas = [titulo]
            for b in t.barcos:
                marca = "✖" if b.hundido else "●"
                lineas.append(f" {marca} {b.nombre} ({len(b.celdas)})")
            return "\n".join(lineas)
        self.lbl_flota_e.configure(text=texto("Flota enemiga:", self.enemigo))
        self.lbl_flota_p.configure(text=texto("Tu flota:", self.propio))

    # ---------- ratón ----------
    def celda_evento(self, ev):
        c = (ev.x - MARGEN) // CELDA
        f = (ev.y - MARGEN) // CELDA
        if 0 <= f < TAM and 0 <= c < TAM and ev.x >= MARGEN and ev.y >= MARGEN:
            return (int(f), int(c))
        return None

    def mover(self, ev):
        pos = self.celda_evento(ev)
        if pos != self.hover:
            self.hover = pos
            if self.esperando:
                self.dibujar("enemigo")

    def quitar_hover(self):
        self.hover = None
        if self.esperando:
            self.dibujar("enemigo")

    def pulso(self):
        self.fase ^= 1
        if self.sugerida and self.esperando:
            self.dibujar("enemigo")
        self.after(300, self.pulso)

    # ---------- dibujo ----------
    def redibujar(self):
        self.dibujar("enemigo")
        self.dibujar("propio")

    def dibujar(self, lado):
        cv = self.cv[lado]
        t = self.enemigo if lado == "enemigo" else self.propio
        calor = self.heat[lado]
        barrido = self.scan[lado]
        cv.delete("all")

        # ejes
        for i in range(TAM):
            cv.create_text(MARGEN + i * CELDA + CELDA / 2, MARGEN / 2, text=chr(65 + i),
                           fill=C_TEXTO, font=("Consolas", 9, "bold"))
            cv.create_text(MARGEN / 2, MARGEN + i * CELDA + CELDA / 2, text=str(i + 1),
                           fill=C_TEXTO, font=("Consolas", 9, "bold"))

        maximo = max(max(fila) for fila in calor) if calor else 0
        limite = None if barrido is None else barrido * TAM * CELDA
        mostrar_barcos = (lado == "propio") or self.revelar

        for f in range(TAM):
            for c in range(TAM):
                x0, y0 = MARGEN + c * CELDA, MARGEN + f * CELDA
                x1, y1 = x0 + CELDA, y0 + CELDA
                e = t.disparos.get((f, c), DESCONOCIDO)

                fill, ratio = C_AGUA, 0.0
                if calor and maximo > 0 and e == DESCONOCIDO:
                    if limite is None or f * CELDA + CELDA / 2 <= limite:
                        ratio = calor[f][c] / maximo
                        fill = color_calor(ratio, lado)
                if e == HUNDIDO:
                    fill = C_HUNDIDO
                cv.create_rectangle(x0, y0, x1, y1, fill=fill, outline=C_GRID)

                if mostrar_barcos and (f, c) in t.ocupadas and e == DESCONOCIDO:
                    cv.create_rectangle(x0 + 5, y0 + 5, x1 - 5, y1 - 5, fill=C_BARCO,
                                        outline="#9db6cf")
                if e == AGUA:
                    cv.create_oval(x0 + 14, y0 + 14, x1 - 14, y1 - 14, fill="#8fd0ff", outline="")
                elif e == TOCADO:
                    cv.create_oval(x0 + 7, y0 + 7, x1 - 7, y1 - 7, fill=C_ROJO, outline="#ffb347",
                                   width=2)
                    cv.create_oval(x0 + 14, y0 + 14, x1 - 14, y1 - 14, fill="#ffd27a", outline="")
                elif e == HUNDIDO:
                    cv.create_line(x0 + 8, y0 + 8, x1 - 8, y1 - 8, fill="#ff8a80", width=3)
                    cv.create_line(x0 + 8, y1 - 8, x1 - 8, y0 + 8, fill="#ff8a80", width=3)

                if lado == "enemigo" and ratio >= 0.6:
                    cv.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=str(int(ratio * 100)),
                                   fill="#04210f", font=("Consolas", 9, "bold"))

        # casilla bajo el ratón
        if lado == "enemigo" and self.esperando and self.hover:
            f, c = self.hover
            if (f, c) not in t.disparos:
                x0, y0 = MARGEN + c * CELDA, MARGEN + f * CELDA
                cv.create_rectangle(x0 + 1, y0 + 1, x0 + CELDA - 1, y0 + CELDA - 1,
                                    outline="#ffffff", width=2)

        # casilla sugerida por la IA (parpadea)
        if lado == "enemigo" and self.sugerida and self.esperando and barrido is None:
            f, c = self.sugerida
            x0, y0 = MARGEN + c * CELDA, MARGEN + f * CELDA
            cv.create_rectangle(x0 + 2, y0 + 2, x0 + CELDA - 2, y0 + CELDA - 2,
                                outline="#ffe14d" if self.fase else "#fff7b0",
                                width=4 if self.fase else 2)

        # línea del escáner con estela
        if barrido is not None:
            y = MARGEN + barrido * TAM * CELDA
            base = C_VERDE if lado == "enemigo" else C_ROJO
            for i in range(12):
                yy = max(MARGEN, y - i * 3)
                cv.create_line(MARGEN, yy, MARGEN + TAM * CELDA, yy,
                               fill=mezclar(C_PANEL, base, 1 - i / 12), width=3)


if __name__ == "__main__":
    App().mainloop()
    