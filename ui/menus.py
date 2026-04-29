"""
Pantalla de menú principal, instrucciones y fin de juego.
"""

import pygame
from . import theme as T
from . import widgets


def _draw_background(screen):
    """Fondo con gradiente vertical sutil."""
    h = screen.get_height()
    for i in range(h):
        t = i / h
        r = int(T.BG_GRAD_TOP[0] * (1 - t) + T.BG_GRAD_BOT[0] * t)
        g = int(T.BG_GRAD_TOP[1] * (1 - t) + T.BG_GRAD_BOT[1] * t)
        b = int(T.BG_GRAD_TOP[2] * (1 - t) + T.BG_GRAD_BOT[2] * t)
        pygame.draw.line(screen, (r, g, b), (0, i), (screen.get_width(), i))


class Menu:
    """Menú principal."""

    MODE_HUMAN = "human_vs_human"
    MODE_AI = "human_vs_ai"

    def __init__(self, font_title, font_btn, font_small):
        self.font_title = font_title
        self.font_btn = font_btn
        self.font_small = font_small
        self.choice = None
        self.show_instructions = False
        cx = T.WIN_W // 2 - 175
        cy = 320
        self.btn_human = widgets.Button((cx, cy, 350, 64), "Humano vs Humano",
                                        callback=lambda: self._set(self.MODE_HUMAN), font=font_btn)
        self.btn_ai = widgets.Button((cx, cy + 80, 350, 64), "Humano vs IA",
                                     callback=lambda: self._set(self.MODE_AI), font=font_btn)
        self.btn_inst = widgets.Button((cx, cy + 160, 350, 64), "Instrucciones",
                                       callback=self._toggle_instructions, font=font_btn)
        self.btn_quit = widgets.Button((cx, cy + 240, 350, 64), "Salir",
                                       callback=lambda: self._set("quit"), font=font_btn)

    def _set(self, choice):
        self.choice = choice

    def _toggle_instructions(self):
        self.show_instructions = not self.show_instructions

    def handle(self, event):
        if self.show_instructions:
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                self.show_instructions = False
            return
        for b in (self.btn_human, self.btn_ai, self.btn_inst, self.btn_quit):
            b.handle(event)

    def draw(self, screen):
        _draw_background(screen)
        # Título principal
        title = self.font_title.render("The Royal Game of Ur", True, T.ACCENT)
        screen.blit(title, ((T.WIN_W - title.get_width()) // 2, 130))
        # Subtítulo
        sub = self.font_small.render("Análisis EEO aplicado — Inteligencia Artificial", True, T.TEXT_DIM)
        screen.blit(sub, ((T.WIN_W - sub.get_width()) // 2, 210))
        # Línea decorativa
        line_y = 250
        line_w = 400
        pygame.draw.line(screen, T.ACCENT_DIM,
                         ((T.WIN_W - line_w) // 2, line_y),
                         ((T.WIN_W + line_w) // 2, line_y), 2)
        # Pequeña roseta decorativa central
        pygame.draw.circle(screen, T.ACCENT, (T.WIN_W // 2, line_y), 6)

        if self.show_instructions:
            self._draw_instructions(screen)
            return

        for b in (self.btn_human, self.btn_ai, self.btn_inst, self.btn_quit):
            b.draw(screen)

    def _draw_instructions(self, screen):
        rect = pygame.Rect(T.WIN_W // 2 - 420, 280, 840, 460)
        pygame.draw.rect(screen, T.PANEL_BG, rect, border_radius=14)
        pygame.draw.rect(screen, T.ACCENT, rect, width=2, border_radius=14)

        lines = [
            ("REGLAS DEL JUEGO", True),
            ("", False),
            ("• Cada jugador tiene 4 fichas que deben recorrer un camino de 14 casillas hasta la Meta.", False),
            ("• En tu turno lanzas 4 dados tetraédricos: cada uno da 0 o 1.", False),
            ("  La suma indica cuántas casillas mueves UNA ficha a tu elección.", False),
            ("• Si una ficha cae en una ROSETA, obtienes un turno extra.", False),
            ("• La roseta del centro (8) es SEGURA: una ficha ahí no puede ser capturada.", False),
            ("• Si caes en una casilla de la zona compartida ocupada por el rival,", False),
            ("  lo capturas y su ficha vuelve a su reserva.", False),
            ("• No puedes caer sobre una ficha tuya.", False),
            ("• Para llevar una ficha a la Meta necesitas la suma EXACTA.", False),
            ("• Si la suma de los dados es 0, pierdes el turno.", False),
            ("• Gana el primer jugador que lleve sus 4 fichas a la Meta.", False),
            ("", False),
            ("(Click o tecla para volver al menú)", False),
        ]
        y = rect.y + 24
        for line, is_title in lines:
            color = T.ACCENT if is_title else T.TEXT
            font = self.font_small if not is_title else pygame.font.SysFont("arial", 22, bold=True)
            screen.blit(font.render(line, True, color), (rect.x + 28, y))
            y += 28 if is_title else 26


class GameOverScreen:
    def __init__(self, winner, font_title, font_btn):
        self.winner = winner
        self.font_title = font_title
        self.font_btn = font_btn
        self.choice = None
        cx = T.WIN_W // 2 - 175
        cy = T.WIN_H // 2 + 60
        self.btn_again = widgets.Button((cx, cy, 350, 64), "Jugar de nuevo",
                                        callback=lambda: self._set("again"), font=font_btn)
        self.btn_menu = widgets.Button((cx, cy + 80, 350, 64), "Menú principal",
                                       callback=lambda: self._set("menu"), font=font_btn)

    def _set(self, choice):
        self.choice = choice

    def handle(self, event):
        self.btn_again.handle(event)
        self.btn_menu.handle(event)

    def draw(self, screen):
        overlay = pygame.Surface((T.WIN_W, T.WIN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))
        msg = f"¡Gana el Jugador {self.winner}!"
        title = self.font_title.render(msg, True, T.ACCENT)
        screen.blit(title, ((T.WIN_W - title.get_width()) // 2, T.WIN_H // 2 - 80))
        # Línea decorativa
        line_y = T.WIN_H // 2 - 10
        line_w = 300
        pygame.draw.line(screen, T.ACCENT_DIM,
                         ((T.WIN_W - line_w) // 2, line_y),
                         ((T.WIN_W + line_w) // 2, line_y), 2)
        self.btn_again.draw(screen)
        self.btn_menu.draw(screen)
