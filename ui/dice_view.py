"""
Render de los 4 dados.
Cada dado se dibuja como un cuadrado con o sin un punto (1 o 0).
"""

import pygame
from . import theme as T


def draw_dice(screen, state, font, x=60, y=620):
    """Dibuja los 4 dados a partir de la posicion (x,y) y muestra la suma."""
    size = 50
    gap = 12

    for i, val in enumerate(state.dice):
        rect = pygame.Rect(x + i * (size + gap), y, size, size)
        pygame.draw.rect(screen, T.DICE_BG, rect, border_radius=8)
        pygame.draw.rect(screen, T.DICE_BORDER, rect, width=2, border_radius=8)

        if val == 1:
            cx, cy = rect.center
            pygame.draw.circle(screen, T.DICE_DOT, (cx, cy), 8)

        # numero del dado
        idx = font.render(f"D{i+1}", True, T.TEXT_DIM)
        screen.blit(idx, (rect.x + 4, rect.bottom + 2))

    # Suma
    label_x = x + 4 * (size + gap) + 20
    if state.dice_rolled:
        label = f"ΣD = {state.dice_sum}"
    else:
        label = "Lanza los dados"
    txt = font.render(label, True, T.ACCENT)
    screen.blit(txt, (label_x, y + 12))
