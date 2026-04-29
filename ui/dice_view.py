"""
Render de los 4 dados tetraédricos (representados como triángulos).
Los dados originales del Ur son tetraedros con 2 vértices marcados.
Aquí se representan como triángulos: marcado (con punto) o no.
"""

import pygame
from . import theme as T


def draw_dice(screen, state, font, x=60, y=620):
    """Dibuja los 4 dados como triángulos a partir de la posición (x,y) y muestra la suma."""
    size = 56
    gap = 14

    # Caja de fondo
    box_w = 4 * (size + gap) + 240
    box_rect = pygame.Rect(x - 12, y - 12, box_w, size + 60)
    pygame.draw.rect(screen, T.PANEL_BG, box_rect, border_radius=10)
    pygame.draw.rect(screen, T.PANEL_BORDER, box_rect, width=2, border_radius=10)

    # Etiqueta
    label = font.render("Dados", True, T.ACCENT)
    screen.blit(label, (x, y - 8))
    y_dice = y + 14

    for i, val in enumerate(state.dice):
        dx = x + i * (size + gap)
        # Dibujar triángulo (tetraedro visto desde arriba)
        points = [
            (dx + size // 2, y_dice + 4),         # vértice superior
            (dx + 4, y_dice + size - 4),          # inferior izq
            (dx + size - 4, y_dice + size - 4),   # inferior der
        ]
        # Sombra
        shadow_pts = [(p[0] + 2, p[1] + 3) for p in points]
        pygame.draw.polygon(screen, (0, 0, 0), shadow_pts)
        # Cuerpo
        pygame.draw.polygon(screen, T.DICE_BG, points)
        pygame.draw.polygon(screen, T.DICE_BORDER, points, width=2)

        # Si está marcado, dibujar un punto en el vértice superior
        if val == 1:
            pygame.draw.circle(screen, T.DICE_DOT, (points[0][0], points[0][1] + 14), 6)

        # Etiqueta D1, D2, ...
        idx = font.render(f"D{i+1}", True, T.TEXT_DIM)
        screen.blit(idx, (dx + size // 2 - idx.get_width() // 2, y_dice + size + 2))

    # Suma
    label_x = x + 4 * (size + gap) + 20
    if state.dice_rolled:
        sum_label = f"Σ = {state.dice_sum}"
        font_big = pygame.font.SysFont("arial", 32, bold=True)
        txt = font_big.render(sum_label, True, T.ACCENT)
        screen.blit(txt, (label_x, y_dice + 8))
    else:
        txt = font.render("Lanza los dados", True, T.TEXT_DIM)
        screen.blit(txt, (label_x, y_dice + 18))
