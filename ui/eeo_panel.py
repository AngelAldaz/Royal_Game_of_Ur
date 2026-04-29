"""
Panel lateral que muestra el vector de estado EEO actualizado en tiempo real,
tal como en la Tabla de Estados del 3.1:

  Ur = ((R1,M1),(R2,M2)) . ((n,J,S,P) x 8) . (D1,D2,D3,D4) . (tau, sumD) . ((O,U,rho) x 20)
"""

import pygame
from game import constants as C
from . import theme as T
from . import widgets


def draw_panel(screen, state, font_big, font_small, font_tiny):
    rect = pygame.Rect(T.PANEL_X, T.PANEL_Y, T.PANEL_W, T.PANEL_H)
    pygame.draw.rect(screen, T.PANEL_BG, rect, border_radius=10)
    pygame.draw.rect(screen, T.TILE_BORDER, rect, width=2, border_radius=10)

    x = rect.x + 16
    y = rect.y + 12

    # Titulo
    screen.blit(font_big.render("Vector de Estado EEO", True, T.ACCENT), (x, y))
    y += 32
    screen.blit(font_small.render("Ur = (J)·(F)·(D)·(T)·(C)", True, T.TEXT_DIM), (x, y))
    y += 24

    # Jugadores
    y = _section(screen, "Jugadores  (R, M)", x, y, font_small)
    j1 = state.players_reserva[C.J1], state.players_meta[C.J1]
    j2 = state.players_reserva[C.J2], state.players_meta[C.J2]
    text = f"J1 = {j1}    J2 = {j2}"
    screen.blit(font_small.render(text, True, T.TEXT), (x + 8, y))
    y += 24

    # Tablero
    y = _section(screen, "Tablero  (τ, ΣD)", x, y + 6, font_small)
    tau = "–" if not state.dice_rolled and state.last_event == "Inicio del juego" else f"J{state.turn}"
    text = f"τ = J{state.turn}    ΣD = {state.dice_sum}"
    screen.blit(font_small.render(text, True, T.TEXT), (x + 8, y))
    y += 24

    # Dados
    y = _section(screen, "Dados  (D1, D2, D3, D4)", x, y + 6, font_small)
    text = f"({state.dice[0]}, {state.dice[1]}, {state.dice[2]}, {state.dice[3]})"
    screen.blit(font_small.render(text, True, T.TEXT), (x + 8, y))
    y += 24

    # Fichas J1
    y = _section(screen, "Fichas J1  (n, J, S, P)", x, y + 6, font_tiny)
    for p in state.pieces_of(C.J1):
        text = f"({p.number}, J1, {p.state}, {p.position})"
        screen.blit(font_tiny.render(text, True, T.TEXT), (x + 8, y))
        y += 18

    # Fichas J2
    y = _section(screen, "Fichas J2  (n, J, S, P)", x, y + 6, font_tiny)
    for p in state.pieces_of(C.J2):
        text = f"({p.number}, J2, {p.state}, {p.position})"
        screen.blit(font_tiny.render(text, True, T.TEXT), (x + 8, y))
        y += 18

    # Casillas
    y = _section(screen, "Casillas  (O, U, ρ)", x, y + 6, font_tiny)
    for sq in range(1, 21):
        occ = state.ocupantes[sq]
        owner = "vacío" if occ == 0 else f"J{occ}"
        rho = "SI" if C.is_rosette(sq) else "NO"
        text = f"({owner}, {sq}, {rho})"
        col = sq // 11  # 0..1
        row = (sq - 1) % 10
        cx = x + 8 + col * 220
        cy = y + row * 18
        screen.blit(font_tiny.render(text, True, T.TEXT), (cx, cy))

    y_after_casillas = y + 10 * 18 + 8

    # Ultimo evento
    y = _section(screen, "Último operador aplicado", x, y_after_casillas, font_small)
    widgets.render_text_wrapped(
        screen, state.last_event,
        pygame.Rect(x + 8, y, T.PANEL_W - 32, 80),
        font_tiny, color=T.ACCENT
    )


def _section(screen, title, x, y, font):
    screen.blit(font.render(title, True, T.ACCENT), (x, y))
    return y + font.get_height() + 4
