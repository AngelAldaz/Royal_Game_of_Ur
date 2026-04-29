"""
Render del tablero, fichas, reservas/metas e indicadores de turno.
"""

import math
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

    # Borde exterior del tablero (tipo madera)
    bw = T.BOARD_COLS * (T.TILE_SIZE + T.TILE_GAP) - T.TILE_GAP
    bh = T.BOARD_ROWS * (T.TILE_SIZE + T.TILE_GAP) - T.TILE_GAP
    border_rect = pygame.Rect(T.BOARD_X - 14, T.BOARD_Y - 14, bw + 28, bh + 28)
    pygame.draw.rect(screen, T.BOARD_BG, border_rect, border_radius=14)
    pygame.draw.rect(screen, T.BOARD_BORDER, border_rect, width=3, border_radius=14)

    # Casillas
    for sq in T.SQUARE_GRID:
        _draw_tile(screen, sq)

    # Highlights (movimientos legales)
    for sq, color in highlights:
        if sq is None or sq not in T.SQUARE_GRID:
            continue
        rect = square_rect(sq)
        # Marco brillante con grosor pulsante
        pygame.draw.rect(screen, color, rect.inflate(6, 6), width=4, border_radius=10)

    # Fichas en el tablero
    for piece in state.pieces:
        if piece.state != C.ACTIVA:
            continue
        sq = piece.square()
        if sq is None:
            continue
        cx, cy = square_center(sq)
        _draw_piece(screen, cx, cy, piece.owner, piece.number, font_small)

    # Reservas y metas
    _draw_reserve_meta(screen, state, font_small)

    # Indicador de turno (parte superior)
    _draw_turn_indicator(screen, state, font_small, ai_thinking)


def _draw_tile(screen, sq):
    """Dibuja una casilla, con su decoración si es roseta."""
    rect = square_rect(sq)
    is_rosette = C.is_rosette(sq)
    is_safe = (sq == C.ROSETA_SEGURA)

    if is_safe:
        base_color = T.ROSETTE_SAFE
        dot_color = T.ROSETTE_SAFE_DOT
    elif is_rosette:
        base_color = T.ROSETTE
        dot_color = T.ROSETTE_DOT
    else:
        base_color = T.TILE
        dot_color = None

    # Sombra interna sutil
    shadow_rect = rect.move(2, 2)
    pygame.draw.rect(screen, (0, 0, 0, 80), shadow_rect, border_radius=10)
    pygame.draw.rect(screen, base_color, rect, border_radius=10)
    pygame.draw.rect(screen, T.TILE_BORDER, rect, width=2, border_radius=10)

    # Dibujar el símbolo de roseta (5 puntos en cruz)
    if is_rosette:
        cx, cy = rect.center
        r = 5
        # punto central + 4 alrededor
        pygame.draw.circle(screen, dot_color, (cx, cy), r)
        offsets = [(0, -22), (0, 22), (-22, 0), (22, 0)]
        for ox, oy in offsets:
            pygame.draw.circle(screen, dot_color, (cx + ox, cy + oy), r - 1)
        # líneas conectoras suaves
        pygame.draw.line(screen, dot_color, (cx, cy - 20), (cx, cy + 20), 2)
        pygame.draw.line(screen, dot_color, (cx - 20, cy), (cx + 20, cy), 2)


def _draw_piece(screen, cx, cy, owner, number, font, radius=24):
    """Dibuja una ficha como disco con sombra y número."""
    if owner == C.J1:
        base = T.J1_COLOR
        highlight = T.J1_HIGHLIGHT
        shadow = T.J1_SHADOW
        num_color = T.J1_NUMBER
    else:
        base = T.J2_COLOR
        highlight = T.J2_HIGHLIGHT
        shadow = T.J2_SHADOW
        num_color = T.J2_NUMBER

    # Sombra (offset abajo)
    pygame.draw.circle(screen, (0, 0, 0), (cx + 2, cy + 3), radius)
    # Aro exterior
    pygame.draw.circle(screen, shadow, (cx, cy), radius)
    # Cuerpo
    pygame.draw.circle(screen, base, (cx, cy), radius - 2)
    # Highlight superior izquierdo (efecto 3D)
    pygame.draw.circle(screen, highlight, (cx - radius // 4, cy - radius // 4), radius // 3)
    # Borde delgado
    pygame.draw.circle(screen, shadow, (cx, cy), radius - 2, width=1)

    # Número
    txt = font.render(str(number), True, num_color)
    screen.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))


def _draw_reserve_meta(screen, state, font):
    """Dibuja columnas de reserva y meta a los lados del tablero."""
    bw = T.BOARD_COLS * (T.TILE_SIZE + T.TILE_GAP)

    # Posiciones (centro X de cada columna)
    j1_reserve_cx = 45
    j2_reserve_cx = 45
    j1_meta_cx = T.BOARD_X + bw + 12
    j2_meta_cx = T.BOARD_X + bw + 12

    j1_y = T.BOARD_Y + 5
    j2_y = T.BOARD_Y + (T.TILE_SIZE + T.TILE_GAP) * 2 + 5

    label_font = pygame.font.SysFont("arial", 14, bold=True)

    # Etiquetas centradas sobre cada columna
    def centered_label(text, color, cx, y):
        surf = label_font.render(text, True, color)
        screen.blit(surf, (cx - surf.get_width() // 2, y))

    centered_label("Reserva J1", T.TEXT_DIM, j1_reserve_cx, j1_y - 22)
    centered_label(f"Meta J1: {state.players_meta[C.J1]}/4", T.ACCENT_DIM, j1_meta_cx, j1_y - 22)
    centered_label("Reserva J2", T.TEXT_DIM, j2_reserve_cx, j2_y + T.TILE_SIZE + 4)
    centered_label(f"Meta J2: {state.players_meta[C.J2]}/4", T.ACCENT_DIM, j2_meta_cx, j2_y + T.TILE_SIZE + 4)

    j1_reserve_pieces = [p for p in state.pieces_of(C.J1) if p.state == C.ESPERA]
    j2_reserve_pieces = [p for p in state.pieces_of(C.J2) if p.state == C.ESPERA]
    j1_meta_pieces = [p for p in state.pieces_of(C.J1) if p.state == C.COMPLETADA]
    j2_meta_pieces = [p for p in state.pieces_of(C.J2) if p.state == C.COMPLETADA]

    spacing = 30
    for i, p in enumerate(j1_reserve_pieces):
        _draw_piece(screen, j1_reserve_cx, j1_y + 18 + i * spacing, C.J1, p.number, font, radius=14)
    for i, p in enumerate(j1_meta_pieces):
        _draw_piece(screen, j1_meta_cx, j1_y + 18 + i * spacing, C.J1, p.number, font, radius=14)
    for i, p in enumerate(j2_reserve_pieces):
        _draw_piece(screen, j2_reserve_cx, j2_y + 18 + i * spacing, C.J2, p.number, font, radius=14)
    for i, p in enumerate(j2_meta_pieces):
        _draw_piece(screen, j2_meta_cx, j2_y + 18 + i * spacing, C.J2, p.number, font, radius=14)


def _draw_turn_indicator(screen, state, font, ai_thinking):
    """Banner del turno actual, arriba a la izquierda."""
    box_rect = pygame.Rect(20, 20, 700, 80)
    pygame.draw.rect(screen, T.PANEL_BG, box_rect, border_radius=12)
    pygame.draw.rect(screen, T.PANEL_BORDER, box_rect, width=2, border_radius=12)

    # Indicador circular del jugador en turno
    cx = box_rect.x + 40
    cy = box_rect.centery
    _draw_piece(screen, cx, cy, state.turn, state.turn, font, radius=24)

    # Texto
    msg1 = f"Turno del Jugador {state.turn}"
    if ai_thinking:
        msg2 = "IA pensando..."
    elif state.dice_rolled:
        if state.dice_sum == 0:
            msg2 = "Suma 0 — pasa turno"
        else:
            msg2 = f"Selecciona una ficha para mover {state.dice_sum} casilla{'s' if state.dice_sum != 1 else ''}"
    else:
        msg2 = "Lanza los dados"

    title_font = pygame.font.SysFont("arial", 22, bold=True)
    screen.blit(title_font.render(msg1, True, T.ACCENT), (cx + 40, cy - 22))
    screen.blit(font.render(msg2, True, T.TEXT_DIM), (cx + 40, cy + 8))


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
    cx = 45
    if state.turn == C.J1:
        cy_base = T.BOARD_Y + 5 + 18
    else:
        cy_base = T.BOARD_Y + (T.TILE_SIZE + T.TILE_GAP) * 2 + 5 + 18

    reserve_pieces = [p for p in state.pieces_of(state.turn) if p.state == C.ESPERA]
    for i, p in enumerate(reserve_pieces):
        cy = cy_base + i * 30
        if (mouse_pos[0] - cx) ** 2 + (mouse_pos[1] - cy) ** 2 <= 16 ** 2:
            return p
    return None
