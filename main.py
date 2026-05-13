"""
Punto de entrada del juego.
Implementación en Pygame del Royal Game of Ur, basada en el modelo EEO 3.1.

Modos:
  - Humano vs Humano (mismo teclado/ratón)
  - Humano vs IA (expectiminimax con heurística)

Uso:
    python main.py

Estructura:
  - game/eeo.py    : SOLO Tabla 1 (entidades) y Tabla 2 (operadores).
  - game/rules.py  : reglas derivadas (paths, zonas, roseta segura, helpers).
  - game/engine.py : Game (estado de sesión) + apply_move + legal_moves.
"""

import sys
import time
import pygame

from game import eeo
from game import rules
from game import engine
from game import ai as AI

from ui import theme as T
from ui import board_view, dice_view, eeo_panel, menus, widgets


# Estados de la app
STATE_MENU = "menu"
STATE_PLAY = "play"
STATE_GAMEOVER = "gameover"

# Delays de la IA (segundos) — pensados para que la maestra/jurado vea cada operador
AI_DELAY_BEFORE_ROLL = 1.0   # antes de lanzar dados
AI_DELAY_AFTER_ROLL = 2.0    # después de lanzar (mostrar dados)
AI_DELAY_AFTER_MOVE = 1.5    # después de aplicar el movimiento


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
    legal_moves_list = []

    # Control de la IA
    ai_next_action_at = 0.0       # tiempo unix en el que la IA puede actuar
    ai_phase = "idle"             # idle / waiting_to_roll / waiting_to_move
    auto_pass_until = 0.0         # auto-pasar turno (humano) cuando no hay jugadas

    # Botones
    roll_btn = widgets.Button((60, 700, 200, 50), "Lanzar dados", callback=None, font=font_btn)
    pass_btn = widgets.Button((280, 700, 200, 50), "Pasar turno", callback=None, font=font_btn)

    game_over_screen = None

    running = True
    while running:
        clock.tick(T.FPS)
        now = time.time()

        # ---------------- EVENTOS ----------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if app_state == STATE_MENU:
                menu.handle(event)

            elif app_state == STATE_PLAY:
                is_ai_turn = (mode == menus.Menu.MODE_AI and game_state.τ == eeo.J_2)
                if not is_ai_turn:
                    roll_btn.handle(event)
                    pass_btn.handle(event)
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        _handle_play_click(event.pos, game_state, legal_moves_list)

            elif app_state == STATE_GAMEOVER:
                game_over_screen.handle(event)

        # ---------------- LÓGICA POR ESTADO ----------------
        if app_state == STATE_MENU:
            if menu.choice == "quit":
                running = False
            elif menu.choice in (menus.Menu.MODE_HUMAN, menus.Menu.MODE_AI):
                mode = menu.choice
                game_state = engine.Game()
                app_state = STATE_PLAY
                legal_moves_list = []
                ai_phase = "idle"
                ai_next_action_at = 0.0
                menu.choice = None

        elif app_state == STATE_PLAY:
            # Detección de fin de juego
            if game_state.is_terminal():
                app_state = STATE_GAMEOVER
                game_over_screen = menus.GameOverScreen(game_state.winner, font_title, font_btn)
                continue

            # Asignar callback a roll_btn (referencia al estado actual)
            if roll_btn.callback is None:
                def make_roll_cb(state):
                    def cb():
                        if not state.dice_rolled and not state.is_terminal():
                            engine.lanzar_dados(state)
                    return cb
                roll_btn.callback = make_roll_cb(game_state)

            def make_pass_cb(state):
                def cb():
                    if state.dice_rolled and (state.ΣD == 0 or not engine.legal_moves(state)):
                        engine.perder_turno(state)
                return cb
            pass_btn.callback = make_pass_cb(game_state)

            # ---- TURNO DE LA IA ----
            is_ai_turn = (mode == menus.Menu.MODE_AI and game_state.τ == eeo.J_2)
            if is_ai_turn and not game_state.is_terminal():
                if not game_state.dice_rolled:
                    # Fase 1: la IA va a lanzar dados
                    if ai_phase != "waiting_to_roll":
                        ai_phase = "waiting_to_roll"
                        ai_next_action_at = now + AI_DELAY_BEFORE_ROLL
                    elif now >= ai_next_action_at:
                        engine.lanzar_dados(game_state)
                        ai_phase = "waiting_to_move"
                        ai_next_action_at = now + AI_DELAY_AFTER_ROLL
                else:
                    # Fase 2: la IA va a mover (o pasar turno si no hay jugadas)
                    if ai_phase != "waiting_to_move":
                        ai_phase = "waiting_to_move"
                        ai_next_action_at = now + AI_DELAY_AFTER_ROLL
                    elif now >= ai_next_action_at:
                        moves = engine.legal_moves(game_state)
                        if not moves:
                            engine.perder_turno(game_state)
                        else:
                            chosen = AI.choose_move(game_state, depth=3)
                            if chosen is None:
                                engine.perder_turno(game_state)
                            else:
                                engine.apply_move(game_state, chosen)
                        ai_phase = "idle"
                        ai_next_action_at = now + AI_DELAY_AFTER_MOVE
            else:
                ai_phase = "idle"

            # ---- Movimientos legales y estado de botones ----
            if game_state.dice_rolled and not game_state.is_terminal():
                legal_moves_list = engine.legal_moves(game_state)
                pass_btn.enabled = (game_state.ΣD == 0 or len(legal_moves_list) == 0)
                roll_btn.enabled = False
                # Auto-pasar turno (humano) si no hay jugadas posibles
                is_human_turn = not (mode == menus.Menu.MODE_AI and game_state.τ == eeo.J_2)
                if is_human_turn and pass_btn.enabled:
                    if auto_pass_until == 0.0:
                        auto_pass_until = now + 1.5
                    elif now >= auto_pass_until:
                        engine.perder_turno(game_state)
                        auto_pass_until = 0.0
                else:
                    auto_pass_until = 0.0
            else:
                legal_moves_list = []
                roll_btn.enabled = not game_state.is_terminal() and not is_ai_turn
                pass_btn.enabled = False
                auto_pass_until = 0.0

        elif app_state == STATE_GAMEOVER:
            if game_over_screen.choice == "again":
                game_state = engine.Game()
                app_state = STATE_PLAY
                legal_moves_list = []
                game_over_screen = None
                roll_btn.callback = None
                ai_phase = "idle"
                ai_next_action_at = 0.0
            elif game_over_screen.choice == "menu":
                app_state = STATE_MENU
                menu = menus.Menu(font_title, font_btn, font_small)
                game_state = None
                game_over_screen = None
                roll_btn.callback = None
                ai_phase = "idle"

        # ---------------- RENDER ----------------
        if app_state == STATE_MENU:
            menu.draw(screen)
        else:
            menus._draw_background(screen)
            highlights = _highlights_for(game_state, legal_moves_list)
            is_ai_turn = (mode == menus.Menu.MODE_AI and game_state.τ == eeo.J_2)
            ai_thinking = is_ai_turn and ai_phase != "idle"
            board_view.draw_board(screen, game_state, font_small,
                                  highlights=highlights, ai_thinking=ai_thinking)
            dice_view.draw_dice(screen, game_state, font_small)
            roll_btn.draw(screen)
            pass_btn.draw(screen)
            eeo_panel.draw_panel(screen, game_state, font_big, font_small, font_tiny)

            if app_state == STATE_GAMEOVER and game_over_screen is not None:
                game_over_screen.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


def _highlights_for(state, legal_moves):
    """Devuelve lista de (square, color) para resaltar movimientos legales."""
    out = []
    if not legal_moves or state.ΣD == 0 or not state.dice_rolled:
        return out
    s = state.ΣD
    for piece in legal_moves:
        if piece.S != eeo.ESPERA and piece.S != eeo.ACTIVA:
            continue
        if piece.S == eeo.ESPERA:
            new_P = s
        else:
            new_P = piece.P + s
        if new_P == rules.META_POS or new_P > rules.META_POS:
            continue
        target = rules.square_at(piece.J, new_P)
        if target is None:
            continue
        out.append((target, T.OK_GREEN))
    return out


def _handle_play_click(pos, state, legal_moves):
    """Procesa un click izquierdo durante la fase de juego (turno humano)."""
    if state.is_terminal() or not state.dice_rolled or state.ΣD == 0:
        return

    # Click sobre ficha en reserva
    p_reserve = board_view.reserve_piece_at_pos(state, pos)
    if p_reserve is not None and p_reserve in legal_moves:
        engine.apply_move(state, p_reserve)
        return

    # Click sobre ficha en tablero
    p_board = board_view.piece_at_pos(state, pos)
    if p_board is not None and p_board in legal_moves and p_board.J == state.τ:
        engine.apply_move(state, p_board)
        return


if __name__ == "__main__":
    main()
