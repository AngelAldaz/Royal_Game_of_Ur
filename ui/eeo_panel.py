"""
Panel lateral con el vector de estado EEO en tiempo real.

  Ur = ((R_1, M_1), (R_2, M_2)) . ((n_i, J_i, S_i, P_i)) x 8
       . (D_1, D_2, D_3, D_4) . (τ, ΣD) . ((O_n, U_n, ρ_n)) x 20

Lee directamente los atributos definidos en game/eeo.py:
state.R, state.M, state.F, state.D, state.τ, state.ΣD y state.C[n]
(donde state.C[n] expone .O, .U y .ρ como en la Tabla 1).
"""

import pygame
from game import eeo
from . import theme as T
from . import widgets


def draw_panel(screen, state, font_big, font_small, font_tiny):
    rect = pygame.Rect(T.PANEL_X, T.PANEL_Y, T.PANEL_W, T.PANEL_H)
    pygame.draw.rect(screen, T.PANEL_BG, rect, border_radius=12)
    pygame.draw.rect(screen, T.PANEL_BORDER, rect, width=2, border_radius=12)

    x = rect.x + 18
    y = rect.y + 16

    screen.blit(font_big.render("Vector de Estado EEO", True, T.ACCENT), (x, y))
    y += 30
    screen.blit(font_small.render("Ur = (J)·(F)·(D)·(T)·(C)", True, T.TEXT_DIM), (x, y))
    y += 18
    screen.blit(font_tiny.render("(102 componentes)", True, T.TEXT_DIM), (x, y))
    y += 22

    pygame.draw.line(screen, T.PANEL_BORDER, (x, y), (rect.right - 18, y), 1)
    y += 8

    # Jugadores (R_j, M_j)
    y = _section(screen, "Jugadores  (R_j, M_j)", x, y, font_small)
    j1 = state.R[eeo.J_1], state.M[eeo.J_1]
    j2 = state.R[eeo.J_2], state.M[eeo.J_2]
    text = f"J_1 = {j1}    J_2 = {j2}"
    screen.blit(font_small.render(text, True, T.TEXT), (x + 8, y))
    y += 22

    # Tablero (τ, ΣD)
    y = _section(screen, "Tablero  (τ, ΣD)", x, y + 4, font_small)
    text = f"τ = J_{state.τ}    ΣD = {state.ΣD}"
    screen.blit(font_small.render(text, True, T.TEXT), (x + 8, y))
    y += 22

    # Dados (D_k)
    y = _section(screen, "Dados  (D_1, D_2, D_3, D_4)", x, y + 4, font_small)
    text = f"({state.D[1]}, {state.D[2]}, {state.D[3]}, {state.D[4]})"
    screen.blit(font_small.render(text, True, T.TEXT), (x + 8, y))
    y += 22

    # Fichas J_1 (n_i, J_i, S_i, P_i)
    y = _section(screen, "Fichas J_1  (n_i, J_i, S_i, P_i)", x, y + 4, font_tiny)
    for p in state.pieces_of(eeo.J_1):
        text = f"({p.n}, J_1, {p.S}, {p.P})"
        screen.blit(font_tiny.render(text, True, T.TEXT), (x + 8, y))
        y += 16

    # Fichas J_2
    y = _section(screen, "Fichas J_2  (n_i, J_i, S_i, P_i)", x, y + 4, font_tiny)
    for p in state.pieces_of(eeo.J_2):
        text = f"({p.n}, J_2, {p.S}, {p.P})"
        screen.blit(font_tiny.render(text, True, T.TEXT), (x + 8, y))
        y += 16

    # Casillas (O_n, U_n, ρ_n) — leídas directamente de state.C[n]
    y = _section(screen, "Casillas  (O_n, U_n, ρ_n)", x, y + 4, font_tiny)
    col_w = 220
    for sq in range(1, 21):
        casilla = state.C[sq]
        if casilla.O == eeo.vacío:
            owner_str = "vacío"
            owner_col = T.TEXT_DIM
        else:
            owner_str = f"J_{casilla.O}"
            owner_col = T.TEXT
        ρ_str = "sí" if casilla.ρ else "no"
        text = f"({owner_str}, {casilla.U}, {ρ_str})"
        col = (sq - 1) // 10
        row = (sq - 1) % 10
        cx = x + 8 + col * col_w
        cy = y + row * 16
        screen.blit(font_tiny.render(text, True, owner_col), (cx, cy))

    y_after_casillas = y + 10 * 16 + 6
    pygame.draw.line(screen, T.PANEL_BORDER, (x, y_after_casillas),
                     (rect.right - 18, y_after_casillas), 1)
    y_after_casillas += 6

    _section(screen, "Último operador aplicado", x, y_after_casillas, font_small)
    widgets.render_text_wrapped(
        screen, state.last_event,
        pygame.Rect(x + 8, y_after_casillas + 22, T.PANEL_W - 36, 80),
        font_tiny, color=T.ACCENT
    )


def _section(screen, title, x, y, font):
    screen.blit(font.render(title, True, T.ACCENT), (x, y))
    return y + font.get_height() + 4
