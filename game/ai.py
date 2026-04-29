"""
IA del oponente.

Estrategia: Expectiminimax limitado a profundidad 2-3 (turnos del jugador
y nodos de azar para los dados). Con la heurística siguiente:

  + 1000 por completar ficha (MAX juega para ganar)
  + 200 por capturar ficha rival
  + 80 por aterrizar en roseta (turno extra)
  + 40 por aterrizar en la roseta segura 8 (turno extra + segura)
  + progreso lineal: posicion de cada ficha activa
  + 50 por cada ficha en zona privada de salida (13,14 / 19,20)
  - penalizacion por estar en zona compartida vulnerable a captura
  + 15 por cada ficha del rival aun en reserva (le falta progreso)

  - simetricamente, los terminos del rival se restan.

Como hay azar (dados), se usa expectiminimax: en los nodos de azar se
calcula la esperanza ponderada por la probabilidad de cada suma.
"""

import random
from . import constants as C
from . import operators as ops


# Probabilidad de obtener una suma s al lanzar 4 dados binarios
# P(s) = C(4,s) / 16
DICE_PROB = {
    0: 1 / 16,
    1: 4 / 16,
    2: 6 / 16,
    3: 4 / 16,
    4: 1 / 16,
}


# --------- evaluacion heuristica ---------

def evaluate(state, player):
    """Evalua el estado desde el punto de vista del jugador 'player'."""
    if state.winner == player:
        return 100000
    if state.winner is not None:
        return -100000

    score = 0
    enemy = C.opponent(player)

    # Ganancias / desgaste por fichas en meta
    score += 1000 * state.players_meta[player]
    score -= 1000 * state.players_meta[enemy]

    # Reserva del rival -> bueno para nosotros (le falta avanzar)
    score += 15 * state.players_reserva[enemy]
    score -= 15 * state.players_reserva[player]

    # Posicion / progreso de fichas activas
    for piece in state.pieces:
        if piece.state != C.ACTIVA:
            continue
        sq = piece.square()
        weight = 1 if piece.owner == player else -1
        # avance en el camino
        score += weight * (10 * piece.position)
        # bono por estar en privada de salida (segura y cerca de meta)
        if piece.position >= 13:
            score += weight * 50
        # bono por estar en roseta segura
        if sq == C.ROSETA_SEGURA:
            score += weight * 40
        elif C.is_rosette(sq):
            score += weight * 30
        # penalizacion por estar en zona compartida (vulnerable)
        elif C.is_shared(sq):
            score -= weight * 8

    return score


# --------- expectiminimax ---------

def expectiminimax(state, depth, maximizing_player):
    """
    Devuelve (score) del estado bajo expectiminimax.
    'maximizing_player' es la perspectiva fija (el jugador que toma decisiones).

    Estructura:
      - si state.dice_rolled == False  => nodo de azar (esperanza sobre las sumas)
      - si state.dice_rolled == True   => nodo de decisión (jugador en turno elige)
    """
    if state.is_terminal() or depth == 0:
        return evaluate(state, maximizing_player)

    if not state.dice_rolled:
        # Nodo de azar: ponderar por probabilidad de cada suma
        expected = 0.0
        for s, prob in DICE_PROB.items():
            child = state.clone()
            # Setear dados con la suma s (asignación canónica: primeros s = 1)
            child.dice = [1] * s + [0] * (C.NUM_DADOS - s)
            child.dice_rolled = True
            # Si suma 0 -> pierde turno (sin elección)
            if s == 0:
                ops.lose_turn(child)
                expected += prob * expectiminimax(child, depth - 1, maximizing_player)
            else:
                expected += prob * expectiminimax(child, depth, maximizing_player)
        return expected

    # Nodo de decisión
    moves = ops.legal_moves(state)
    if not moves:
        # No hay movimientos legales -> pierde turno
        child = state.clone()
        ops.lose_turn(child)
        return expectiminimax(child, depth - 1, maximizing_player)

    if state.turn == maximizing_player:
        best = float("-inf")
        for piece in moves:
            child = state.clone()
            piece_clone = child.get_piece(piece.owner, piece.number)
            ops.apply_move(child, piece_clone)
            val = expectiminimax(child, depth - 1, maximizing_player)
            if val > best:
                best = val
        return best
    else:
        worst = float("inf")
        for piece in moves:
            child = state.clone()
            piece_clone = child.get_piece(piece.owner, piece.number)
            ops.apply_move(child, piece_clone)
            val = expectiminimax(child, depth - 1, maximizing_player)
            if val < worst:
                worst = val
        return worst


def choose_move(state, depth=2):
    """
    Elige la mejor ficha a mover para el jugador en turno usando expectiminimax.
    Retorna la Piece a mover, o None si no hay movimientos.
    """
    moves = ops.legal_moves(state)
    if not moves:
        return None

    me = state.turn
    best_score = float("-inf")
    best_piece = moves[0]

    for piece in moves:
        child = state.clone()
        piece_clone = child.get_piece(piece.owner, piece.number)
        ops.apply_move(child, piece_clone)
        # despues del movimiento, expectiminimax desde la perspectiva fija de 'me'
        score = expectiminimax(child, depth, me)
        if score > best_score:
            best_score = score
            best_piece = piece

    return best_piece
