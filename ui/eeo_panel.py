"""
Panel lateral con el vector de estado EEO en tiempo real.

  Ur = ((R_1, M_1), (R_2, M_2)) . ((n_i, J_i, S_i, P_i)) x 8
       . (D_1, D_2, D_3, D_4) . (tau, sigma_D) . ((O_n, U_n, rho_n)) x 20

Nombres mostrados en pantalla coinciden con los del análisis EEO 3.1
y con los atributos del código (state.R, state.M, state.F, state.D,
state.tau, state.sigma_D, state.O).
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
    j1 = state.R[C.J1], state.M[C.J1]
    j2 = state.R[C.J2], state.M[C.J2]
    text = f"J1 = {j1}    J2 = {j2}"
    screen.blit(font_small.render(text, True, T.TEXT), (x + 8, y))
    y += 22

    # Tablero (tau, sigma_D)
    y = _section(screen, "Tablero  (τ, ΣD)", x, y + 4, font_small)
    text = f"τ = J{state.tau}    ΣD = {state.sigma_D}"
    screen.blit(font_small.render(text, True, T.TEXT), (x + 8, y))
    y += 22

    # Dados (D_k)
    y = _section(screen, "Dados  (D_1, D_2, D_3, D_4)", x, y + 4, font_small)
    text = f"({state.D[0]}, {state.D[1]}, {state.D[2]}, {state.D[3]})"
    screen.blit(font_small.render(text, True, T.TEXT), (x + 8, y))
    y += 22

    # Fichas J1 (n_i, J_i, S_i, P_i)
    y = _section(screen, "Fichas J1  (n_i, J_i, S_i, P_i)", x, y + 4, font_tiny)
    for p in state.pieces_of(C.J1):
        text = f"({p.n}, J1, {p.S}, {p.P})"
        screen.blit(font_tiny.render(text, True, T.TEXT), (x + 8, y))
        y += 16

    # Fichas J2
    y = _section(screen, "Fichas J2  (n_i, J_i, S_i, P_i)", x, y + 4, font_tiny)
    for p in state.pieces_of(C.J2):
        text = f"({p.n}, J2, {p.S}, {p.P})"
        screen.blit(font_tiny.render(text, True, T.TEXT), (x + 8, y))
        y += 16

    # Casillas (O_n, U_n, rho_n)
    y = _section(screen, "Casillas  (O_n, U_n, ρ_n)", x, y + 4, font_tiny)
    col_w = 220
    for sq in range(1, 21):
        occ = state.O[sq]
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
