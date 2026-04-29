"""
Punto de entrada del juego.
Implementacion en Pygame del Royal Game of Ur, basada en el modelo EEO 3.1.

Modos:
  - Humano vs Humano (mismo teclado/raton)
  - Humano vs IA (expectiminimax con heuristica)

Uso:
    python main.py
"""

import sys
import time
import pygame

from game import constants as C
from game.state import GameState
from game import operators as ops
from game import ai as AI

from ui import theme as T
from ui import board_view, dice_view, eeo_panel, menus, widgets


# Estados de la app
STATE_MENU = "menu"
STATE_PLAY = "play"
STATE_GAMEOVER = "gameover"


def main():
    pygame.init()
    pygame.display.set_caption("The Royal Game of Ur — Análisis EEO")
    screen = pygame.display.set_mode((T.WIN_W, T.WIN_H))
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont("arial", 56, bold=True)
    font_big = pygame.font.SysFont("arial", 22, bold=True)
    font_btn = pygame.font.SysFont("arial", 24, bold=True)
    font_small = pygame.font.SysFont("arial", 18)
    font_tiny = pygame.font.SysFont("consolas", 13)

    app_state = STATE_MENU
    menu = menus.Menu(font_title, font_btn, font_small)
    game_state = None
    mode = None
    selected_piece = None
    legal_moves_list = []
    ai_thinking_until = 0.0  # tiempo unix hasta el cual la IA "piensa"
    pending_ai_action = False
    auto_pass_until = 0.0    # auto-pasar turno cuando suma=0 o no hay jugadas (humano)

    # Boton: Lanzar dados
    roll_btn = widgets.Button((60, 700, 200, 50), "Lanzar dados", callback=None, font=font_btn)
    pass_btn = widgets.Button((280, 700, 200, 50), "Pasar turno", callback=None, font=font_btn)

    game_over_screen = None

    running = True
    while running:
        dt = clock.tick(T.FPS)
        now = time.time()

        # ---------------- EVENTOS ----------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if app_state == STATE_MENU:
                menu.handle(event)

            elif app_state == STATE_PLAY:
                # Si es turno de la IA, ignoramos eventos del raton durante el "pensamiento"
                is_ai_turn = (mode == menus.Menu.MODE_AI and game_state.turn == C.J2)
                if not is_ai_turn:
                    roll_btn.handle(event)
                    pass_btn.handle(event)
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        _handle_play_click(event.pos, game_state, legal_moves_list)

            elif app_state == STATE_GAMEOVER:
                game_over_screen.handle(event)

        # ---------------- LOGICA POR ESTADO ----------------
        if app_state == STATE_MENU:
            if menu.choice == "quit":
                running = False
            elif menu.choice in (menus.Menu.MODE_HUMAN, menus.Menu.MODE_AI):
                mode = menu.choice
                game_state = GameState()
                app_state = STATE_PLAY
                selected_piece = None
                legal_moves_list = []
                menu.choice = None

        elif app_state == STATE_PLAY:
            # Auto-detectar fin de juego
            if game_state.is_terminal():
                app_state = STATE_GAMEOVER
                game_over_screen = menus.GameOverScreen(game_state.winner, font_title, font_btn)
                continue

            # Boton: lanzar
            if roll_btn.callback is None:
                # asignamos callback que cierra sobre game_state
                def make_roll_cb(state):
                    def cb():
                        if not state.dice_rolled and not state.is_terminal():
                            ops.roll_dice(state)
                    return cb
                roll_btn.callback = make_roll_cb(game_state)
                roll_btn.callback.__name__ = "roll"

            # Pasar turno (solo si suma=0 o sin movimientos legales)
            def make_pass_cb(state):
                def cb():
                    if state.dice_rolled and (state.dice_sum == 0 or not ops.legal_moves(state)):
                        ops.lose_turn(state)
                return cb
            pass_btn.callback = make_pass_cb(game_state)

            # IA (procesar antes de calcular highlights/legal_moves)
            is_ai_turn = (mode == menus.Menu.MODE_AI and game_state.turn == C.J2)
            if is_ai_turn and not game_state.is_terminal():
                if not pending_ai_action:
                    ai_thinking_until = now + 0.6   # pequena pausa visual
                    pending_ai_action = True

                if now >= ai_thinking_until:
                    if not game_state.dice_rolled:
                        ops.roll_dice(game_state)
                    else:
                        moves = ops.legal_moves(game_state)
                        if not moves:
                            ops.lose_turn(game_state)
                        else:
                            chosen = AI.choose_move(game_state, depth=2)
                            if chosen is None:
                                ops.lose_turn(game_state)
                            else:
                                ops.apply_move(game_state, chosen)
                    pending_ai_action = False
                    ai_thinking_until = now + 0.4  # pequena pausa entre lanzar y mover

            # Movimientos legales actuales (para resaltar) — calcular DESPUES de la IA
            if game_state.dice_rolled and not game_state.is_terminal():
                legal_moves_list = ops.legal_moves(game_state)
                pass_btn.enabled = (game_state.dice_sum == 0 or len(legal_moves_list) == 0)
                roll_btn.enabled = False
                # Auto-pasar turno (humano) si no hay nada que hacer
                is_human_turn = not (mode == menus.Menu.MODE_AI and game_state.turn == C.J2)
                if is_human_turn and pass_btn.enabled:
                    if auto_pass_until == 0.0:
                        auto_pass_until = now + 1.2
                    elif now >= auto_pass_until:
                        ops.lose_turn(game_state)
                        auto_pass_until = 0.0
                else:
                    auto_pass_until = 0.0
            else:
                legal_moves_list = []
                roll_btn.enabled = not game_state.is_terminal()
                pass_btn.enabled = False
                auto_pass_until = 0.0

        elif app_state == STATE_GAMEOVER:
            if game_over_screen.choice == "again":
                game_state = GameState()
                app_state = STATE_PLAY
                selected_piece = None
                legal_moves_list = []
                game_over_screen = None
                roll_btn.callback = None
            elif game_over_screen.choice == "menu":
                app_state = STATE_MENU
                menu = menus.Menu(font_title, font_btn, font_small)
                game_state = None
                game_over_screen = None
                roll_btn.callback = None

        # ---------------- RENDER ----------------
        screen.fill(T.BG)

        if app_state == STATE_MENU:
            menu.draw(screen)
        else:
            # Tablero + fichas + reservas + turno
            highlights = _highlights_for(game_state, legal_moves_list)
            ai_thinking = (mode == menus.Menu.MODE_AI and game_state.turn == C.J2 and pending_ai_action)
            board_view.draw_board(screen, game_state, font_small, highlights=highlights, ai_thinking=ai_thinking)

            # Dados
            dice_view.draw_dice(screen, game_state, font_small)

            # Botones
            roll_btn.draw(screen)
            pass_btn.draw(screen)

            # Panel EEO
            eeo_panel.draw_panel(screen, game_state, font_big, font_small, font_tiny)

            if app_state == STATE_GAMEOVER and game_over_screen is not None:
                game_over_screen.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


def _highlights_for(state, legal_moves):
    """Devuelve lista de (square, color) para resaltar movimientos legales."""
    out = []
    if not legal_moves or state.dice_sum == 0 or not state.dice_rolled:
        return out
    s = state.dice_sum
    for piece in legal_moves:
        if piece.state != C.ESPERA and piece.state != C.ACTIVA:
            continue
        if piece.state == C.ESPERA:
            new_pos = s
        else:
            new_pos = piece.position + s
        if new_pos == C.META_POS or new_pos > C.META_POS:
            continue  # no hay casilla destino fisica
        target = C.square_at(piece.owner, new_pos)
        if target is None:
            continue
        out.append((target, T.OK_GREEN))
    return out


def _handle_play_click(pos, state, legal_moves):
    """Procesa un click izquierdo durante la fase de juego (turno humano)."""
    if state.is_terminal() or not state.dice_rolled or state.dice_sum == 0:
        return

    # Click sobre ficha en reserva
    p_reserve = board_view.reserve_piece_at_pos(state, pos)
    if p_reserve is not None and p_reserve in legal_moves:
        ops.apply_move(state, p_reserve)
        return

    # Click sobre ficha en tablero
    p_board = board_view.piece_at_pos(state, pos)
    if p_board is not None and p_board in legal_moves and p_board.owner == state.turn:
        ops.apply_move(state, p_board)
        return


if __name__ == "__main__":
    main()
