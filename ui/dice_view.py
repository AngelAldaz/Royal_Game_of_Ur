"""
Render de los 4 dados tetraédricos (D_1..D_4) con su suma ΣD.
"""

import pygame
from . import theme as T


def draw_dice(screen, state, font, x=60, y=620):
    """Dibuja los 4 dados D_1..D_4 y la suma ΣD."""
    size = 56
    gap = 14

    box_w = 4 * (size + gap) + 240
    box_rect = pygame.Rect(x - 12, y - 12, box_w, size + 60)
    pygame.draw.rect(screen, T.PANEL_BG, box_rect, border_radius=10)
    pygame.draw.rect(screen, T.PANEL_BORDER, box_rect, width=2, border_radius=10)

    label = font.render("Dados D_k", True, T.ACCENT)
    screen.blit(label, (x, y - 8))
    y_dice = y + 14

    for k in range(1, 5):
        val = state.D[k]
        dx = x + (k - 1) * (size + gap)
        points = [
            (dx + size // 2, y_dice + 4),
            (dx + 4, y_dice + size - 4),
            (dx + size - 4, y_dice + size - 4),
        ]
        shadow_pts = [(p[0] + 2, p[1] + 3) for p in points]
        pygame.draw.polygon(screen, (0, 0, 0), shadow_pts)
        pygame.draw.polygon(screen, T.DICE_BG, points)
        pygame.draw.polygon(screen, T.DICE_BORDER, points, width=2)

        if val == 1:
            pygame.draw.circle(screen, T.DICE_DOT, (points[0][0], points[0][1] + 14), 6)

        idx = font.render(f"D_{k}", True, T.TEXT_DIM)
        screen.blit(idx, (dx + size // 2 - idx.get_width() // 2, y_dice + size + 2))

    # Suma ΣD
    label_x = x + 4 * (size + gap) + 20
    if state.dice_rolled:
        sum_label = f"ΣD = {state.ΣD}"
        font_big = pygame.font.SysFont("arial", 32, bold=True)
        txt = font_big.render(sum_label, True, T.ACCENT)
        screen.blit(txt, (label_x, y_dice + 8))
    else:
        txt = font.render("Lanza los dados", True, T.TEXT_DIM)
        screen.blit(txt, (label_x, y_dice + 18))
