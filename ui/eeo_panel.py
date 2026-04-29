"""
Panel lateral con el vector de estado EEO en tiempo real.

  Ur = ((R1,M1),(R2,M2)) . ((n,J,S,P) x 8) . (D1,D2,D3,D4) . (tau, sumD) . ((O,U,rho) x 20)
"""

import pygame
from game import constants as C
from . import theme as T
from . import widgets


def draw_panel(screen, state, font_big, font_small, font_tiny):
    rect = pygame.Rect(T.PANEL_X, T.PANEL_Y, T.PANEL_W, T.PANEL_H)
    pygame.draw.rect(screen, T.PANEL_BG, rect, border_radius=12)
    pygame.draw.rect(screen, T.PANEL_BORDER, rect, width=2, border_radius=12)

    x = rect.x + 18
    y = rect.y + 16

    # Titulo
    screen.blit(font_big.render("Vector de Estado EEO", True, T.ACCENT), (x, y))
    y += 30
    formula = "Ur = (J)·(F)·(D)·(T)·(C)"
    screen.blit(font_small.render(formula, True, T.TEXT_DIM), (x, y))
    y += 18
    screen.blit(font_tiny.render("(102 componentes)", True, T.TEXT_DIM), (x, y))
    y += 22

    # Separador
    pygame.draw.line(screen, T.PANEL_BORDER, (x, y), (rect.right - 18, y), 1)
    y += 8

    # Jugadores
    y = _section(screen, "Jugadores  (R, M)", x, y, font_small)
    j1 = state.players_reserva[C.J1], state.players_meta[C.J1]
    j2 = state.players_reserva[C.J2], state.players_meta[C.J2]
    text = f"J1 = {j1}    J2 = {j2}"
    screen.blit(font_small.render(text, True, T.TEXT), (x + 8, y))
    y += 22

    # Tablero
    y = _section(screen, "Tablero  (τ, ΣD)", x, y + 4, font_small)
    text = f"τ = J{state.turn}    ΣD = {state.dice_sum}"
    screen.blit(font_small.render(text, True, T.TEXT), (x + 8, y))
    y += 22

    # Dados
    y = _section(screen, "Dados  (D1, D2, D3, D4)", x, y + 4, font_small)
    text = f"({state.dice[0]}, {state.dice[1]}, {state.dice[2]}, {state.dice[3]})"
    screen.blit(font_small.render(text, True, T.TEXT), (x + 8, y))
    y += 22

    # Fichas J1
    y = _section(screen, "Fichas J1  (n, J, S, P)", x, y + 4, font_tiny)
    for p in state.pieces_of(C.J1):
        text = f"({p.number}, J1, {p.state}, {p.position})"
        screen.blit(font_tiny.render(text, True, T.TEXT), (x + 8, y))
        y += 16

    # Fichas J2
    y = _section(screen, "Fichas J2  (n, J, S, P)", x, y + 4, font_tiny)
    for p in state.pieces_of(C.J2):
        text = f"({p.number}, J2, {p.state}, {p.position})"
        screen.blit(font_tiny.render(text, True, T.TEXT), (x + 8, y))
        y += 16

    # Casillas (en 2 columnas)
    y = _section(screen, "Casillas  (O, U, ρ)", x, y + 4, font_tiny)
    col_w = 220
    for sq in range(1, 21):
        occ = state.ocupantes[sq]
        if occ == 0:
            owner_str = "vacío"
            owner_col = T.TEXT_DIM
        else:
            owner_str = f"J{occ}"
            owner_col = T.TEXT
        rho = "SI" if C.is_rosette(sq) else "NO"
        text = f"({owner_str}, {sq}, {rho})"
        col = (sq - 1) // 10
        row = (sq - 1) % 10
        cx = x + 8 + col * col_w
        cy = y + row * 16
        screen.blit(font_tiny.render(text, True, owner_col), (cx, cy))

    y_after_casillas = y + 10 * 16 + 6

    # Separador
    pygame.draw.line(screen, T.PANEL_BORDER, (x, y_after_casillas),
                     (rect.right - 18, y_after_casillas), 1)
    y_after_casillas += 6

    # Último evento
    _section(screen, "Último operador aplicado", x, y_after_casillas, font_small)
    widgets.render_text_wrapped(
        screen, state.last_event,
        pygame.Rect(x + 8, y_after_casillas + 22, T.PANEL_W - 36, 80),
        font_tiny, color=T.ACCENT
    )


def _section(screen, title, x, y, font):
    screen.blit(font.render(title, True, T.ACCENT), (x, y))
    return y + font.get_height() + 4
