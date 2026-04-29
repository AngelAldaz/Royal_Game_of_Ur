"""
Render del tablero, fichas, reservas/metas e indicadores de turno.
"""

import pygame
from game import constants as C
from . import theme as T


def square_rect(square):
    """Rect del tablero para la casilla dada."""
    col, row = T.SQUARE_GRID[square]
    x = T.BOARD_X + col * (T.TILE_SIZE + T.TILE_GAP)
    y = T.BOARD_Y + row * (T.TILE_SIZE + T.TILE_GAP)
    return pygame.Rect(x, y, T.TILE_SIZE, T.TILE_SIZE)


def square_center(square):
    r = square_rect(square)
    return r.center


def draw_board(screen, state, font_small, highlights=None, ai_thinking=False):
    """
    Dibuja el tablero completo.
    highlights: lista opcional de (square, color) para resaltar casillas.
    """
    highlights = highlights or []

    # Borde exterior del area del tablero
    bw = T.BOARD_COLS * (T.TILE_SIZE + T.TILE_GAP) - T.TILE_GAP
    bh = T.BOARD_ROWS * (T.TILE_SIZE + T.TILE_GAP) - T.TILE_GAP
    border_rect = pygame.Rect(T.BOARD_X - 10, T.BOARD_Y - 10, bw + 20, bh + 20)
    pygame.draw.rect(screen, (45, 38, 30), border_rect, border_radius=12)

    # Casillas
    for sq, (col, row) in T.SQUARE_GRID.items():
        rect = square_rect(sq)
        is_rosette = C.is_rosette(sq)
        if sq == C.ROSETA_SEGURA:
            color = T.ROSETTE_SAFE
        elif is_rosette:
            color = T.ROSETTE
        else:
            color = T.TILE
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, T.TILE_BORDER, rect, width=2, border_radius=8)

        # Numero de casilla y simbolo de roseta
        label = f"{sq}{'✿' if is_rosette else ''}"
        txt = font_small.render(label, True, T.TEXT_DIM)
        screen.blit(txt, (rect.x + 6, rect.y + 4))

    # Highlights (movimientos legales)
    for sq, color in highlights:
        if sq is None or sq not in T.SQUARE_GRID:
            continue
        rect = square_rect(sq)
        pygame.draw.rect(screen, color, rect, width=4, border_radius=8)

    # Fichas en el tablero
    for piece in state.pieces:
        if piece.state != C.ACTIVA:
            continue
        sq = piece.square()
        if sq is None:
            continue
        cx, cy = square_center(sq)
        _draw_piece(screen, cx, cy, piece.owner, piece.number, font_small)

    # Reservas y metas (fuera del tablero)
    _draw_reserve_meta(screen, state, font_small)

    # Indicador de turno
    _draw_turn_indicator(screen, state, font_small, ai_thinking)


def _draw_piece(screen, cx, cy, owner, number, font, radius=22):
    """Dibuja una ficha como circulo con un numero."""
    color = T.J1_COLOR if owner == C.J1 else T.J2_COLOR
    outline = T.J1_OUTLINE if owner == C.J1 else T.J2_OUTLINE
    pygame.draw.circle(screen, color, (cx, cy), radius)
    pygame.draw.circle(screen, outline, (cx, cy), radius, width=3)
    text_color = T.J2_COLOR if owner == C.J1 else T.J1_COLOR
    txt = font.render(str(number), True, text_color)
    screen.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))


def _draw_reserve_meta(screen, state, font):
    """Dibuja columnas de reserva y meta a los lados del tablero."""
    # J1: arriba-derecha, fuera del tablero
    j1_reserve_x = T.BOARD_X - 50
    j1_reserve_y = T.BOARD_Y - 5
    j1_meta_x = T.BOARD_X + (T.TILE_SIZE + T.TILE_GAP) * 8 + 10
    j1_meta_y = T.BOARD_Y - 5

    # J2: abajo
    j2_reserve_x = T.BOARD_X - 50
    j2_reserve_y = T.BOARD_Y + (T.TILE_SIZE + T.TILE_GAP) * 2
    j2_meta_x = T.BOARD_X + (T.TILE_SIZE + T.TILE_GAP) * 8 + 10
    j2_meta_y = T.BOARD_Y + (T.TILE_SIZE + T.TILE_GAP) * 2

    # Etiquetas
    screen.blit(font.render("Reserva J1", True, T.TEXT_DIM), (j1_reserve_x - 30, j1_reserve_y - 22))
    screen.blit(font.render(f"Meta J1: {state.players_meta[C.J1]}", True, T.TEXT_DIM),
                (j1_meta_x - 5, j1_meta_y - 22))
    screen.blit(font.render("Reserva J2", True, T.TEXT_DIM), (j2_reserve_x - 30, j2_reserve_y + T.TILE_SIZE + 4))
    screen.blit(font.render(f"Meta J2: {state.players_meta[C.J2]}", True, T.TEXT_DIM),
                (j2_meta_x - 5, j2_meta_y + T.TILE_SIZE + 4))

    # Dibujar fichas en reserva (apiladas en columna)
    j1_reserve_pieces = [p for p in state.pieces_of(C.J1) if p.state == C.ESPERA]
    j2_reserve_pieces = [p for p in state.pieces_of(C.J2) if p.state == C.ESPERA]
    j1_meta_pieces = [p for p in state.pieces_of(C.J1) if p.state == C.COMPLETADA]
    j2_meta_pieces = [p for p in state.pieces_of(C.J2) if p.state == C.COMPLETADA]

    # Reserva J1 (vertical)
    for i, p in enumerate(j1_reserve_pieces):
        cy = j1_reserve_y + 20 + i * 24
        _draw_piece(screen, j1_reserve_x, cy, C.J1, p.number, font, radius=14)
    # Meta J1
    for i, p in enumerate(j1_meta_pieces):
        cy = j1_meta_y + 20 + i * 24
        _draw_piece(screen, j1_meta_x + 15, cy, C.J1, p.number, font, radius=14)
    # Reserva J2
    for i, p in enumerate(j2_reserve_pieces):
        cy = j2_reserve_y + 20 + i * 24
        _draw_piece(screen, j2_reserve_x, cy, C.J2, p.number, font, radius=14)
    # Meta J2
    for i, p in enumerate(j2_meta_pieces):
        cy = j2_meta_y + 20 + i * 24
        _draw_piece(screen, j2_meta_x + 15, cy, C.J2, p.number, font, radius=14)


def _draw_turn_indicator(screen, state, font, ai_thinking):
    msg = f"Turno: Jugador {state.turn}"
    if ai_thinking:
        msg += "  (IA pensando...)"
    pygame.draw.rect(screen, T.PANEL_BG, pygame.Rect(20, 20, 400, 50), border_radius=8)
    pygame.draw.rect(screen, T.ACCENT, pygame.Rect(20, 20, 400, 50), width=2, border_radius=8)
    color = T.J1_OUTLINE if state.turn == C.J1 else T.J2_OUTLINE
    if state.turn == C.J2:
        color = (180, 180, 200)
    txt = font.render(msg, True, T.ACCENT)
    screen.blit(txt, (32, 35))


def piece_at_pos(state, mouse_pos):
    """Devuelve la ficha cuyo casillero contenga el mouse, o None."""
    for piece in state.pieces:
        if piece.state != C.ACTIVA:
            continue
        sq = piece.square()
        if sq is None:
            continue
        rect = square_rect(sq)
        if rect.collidepoint(mouse_pos):
            return piece
    return None


def reserve_piece_at_pos(state, mouse_pos):
    """Detecta si el click cayó en una ficha de la reserva del jugador en turno."""
    j1_reserve_x = T.BOARD_X - 50
    j1_reserve_y = T.BOARD_Y - 5
    j2_reserve_x = T.BOARD_X - 50
    j2_reserve_y = T.BOARD_Y + (T.TILE_SIZE + T.TILE_GAP) * 2

    if state.turn == C.J1:
        rx, ry = j1_reserve_x, j1_reserve_y + 20
    else:
        rx, ry = j2_reserve_x, j2_reserve_y + 20

    reserve_pieces = [p for p in state.pieces_of(state.turn) if p.state == C.ESPERA]
    for i, p in enumerate(reserve_pieces):
        cy = ry + i * 24
        if (mouse_pos[0] - rx) ** 2 + (mouse_pos[1] - cy) ** 2 <= 14 ** 2:
            return p
    return None
