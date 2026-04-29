"""
IA del oponente.

Estrategia: Expectiminimax con profundidad parametrizada (default 3) y
nodos de azar para los dados.

Heurística mejorada que considera:
  - Progreso lineal de fichas activas
  - Bono por completar fichas
  - Bono fuerte por capturar
  - Bono diferenciado por roseta (extra-turn) y roseta segura (no capturable)
  - Bono por estar en zona privada de salida (cerca de meta)
  - Penalización dinámica por exposición a captura: cuenta amenazas reales
    (cantidad de sumas de dados con las que el rival podría capturar la ficha
    en su próximo turno).
  - Bono por amenazas propias hacia fichas rivales.
  - Reserva del rival pondera positivo (le falta progresar).

Como hay azar (4 dados binarios → suma 0..4 con probabilidades binomiales),
se usa expectiminimax: en los nodos de azar se calcula la esperanza ponderada
por la probabilidad de cada suma.
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
    """Evalúa el estado desde el punto de vista del jugador 'player'."""
    if state.winner == player:
        return 100000
    if state.winner is not None:
        return -100000

    score = 0
    enemy = C.opponent(player)

    # Fichas en meta
    score += 1200 * state.players_meta[player]
    score -= 1200 * state.players_meta[enemy]

    # Reserva del rival -> bueno para nosotros (le falta avanzar)
    score += 12 * state.players_reserva[enemy]
    score -= 12 * state.players_reserva[player]

    # Posicion / progreso de fichas activas
    for piece in state.pieces:
        if piece.state != C.ACTIVA:
            continue
        sq = piece.square()
        weight = 1 if piece.owner == player else -1
        # avance en el camino (no lineal: posiciones más altas valen más)
        score += weight * (8 * piece.position + (piece.position - 8) ** 2 if piece.position >= 8 else 8 * piece.position)
        # bono por estar en privada de salida
        if piece.position >= 13:
            score += weight * 60
        # bono por estar en roseta
        if sq == C.ROSETA_SEGURA:
            score += weight * 50  # roseta + segura
        elif C.is_rosette(sq):
            score += weight * 35

    # Análisis dinámico de amenazas y oportunidades en zona compartida
    score += _threat_score(state, player)

    return score


def _threat_score(state, player):
    """
    Para cada ficha propia activa en zona compartida (no segura), calcula
    cuántos resultados de dados del rival la pueden capturar en su próximo
    turno. Hace lo mismo para fichas rivales (oportunidades para nosotros).
    """
    score = 0
    enemy = C.opponent(player)

    # Fichas propias en zona vulnerable
    for piece in state.pieces:
        if piece.state != C.ACTIVA:
            continue
        sq = piece.square()
        if not C.is_shared(sq) or sq == C.ROSETA_SEGURA:
            continue

        weight = -1 if piece.owner == player else 1  # exposición propia es mala
        # Calcular cuántas sumas de dados (0..4) permitirían al rival capturar
        threats_prob = 0.0
        owner = C.opponent(piece.owner)  # quién amenaza
        for s, prob in DICE_PROB.items():
            if s == 0:
                continue
            # ¿Hay alguna ficha del rival que pueda llegar a esta casilla con suma s?
            for rival_piece in state.pieces:
                if rival_piece.owner != owner:
                    continue
                if rival_piece.state == C.ESPERA:
                    new_pos = s
                elif rival_piece.state == C.ACTIVA:
                    new_pos = rival_piece.position + s
                else:
                    continue
                if new_pos > C.META_POS or new_pos == C.META_POS:
                    continue
                if C.square_at(rival_piece.owner, new_pos) == sq:
                    threats_prob += prob
                    break  # una amenaza por suma es suficiente

        # threats_prob ∈ [0..1], peso 60 para amenaza máxima
        score += weight * int(60 * threats_prob)

    return score


# --------- expectiminimax ---------

def expectiminimax(state, depth, maximizing_player, alpha=float("-inf"), beta=float("inf")):
    """
    Devuelve (score) del estado bajo expectiminimax.
    'maximizing_player' es la perspectiva fija (el jugador que toma decisiones).

    Estructura:
      - si state.dice_rolled == False  => nodo de azar (esperanza sobre las sumas)
      - si state.dice_rolled == True   => nodo de decisión (jugador en turno elige)

    alpha/beta solo se usa en nodos de decisión (no en los de azar).
    """
    if state.is_terminal() or depth == 0:
        return evaluate(state, maximizing_player)

    if not state.dice_rolled:
        # Nodo de azar: ponderar por probabilidad de cada suma
        expected = 0.0
        for s, prob in DICE_PROB.items():
            child = state.clone()
            child.dice = [1] * s + [0] * (C.NUM_DADOS - s)
            child.dice_rolled = True
            if s == 0:
                ops.lose_turn(child)
                expected += prob * expectiminimax(child, depth - 1, maximizing_player)
            else:
                expected += prob * expectiminimax(child, depth, maximizing_player)
        return expected

    # Nodo de decisión
    moves = ops.legal_moves(state)
    if not moves:
        child = state.clone()
        ops.lose_turn(child)
        return expectiminimax(child, depth - 1, maximizing_player)

    if state.turn == maximizing_player:
        best = float("-inf")
        for piece in moves:
            child = state.clone()
            piece_clone = child.get_piece(piece.owner, piece.number)
            ops.apply_move(child, piece_clone)
            val = expectiminimax(child, depth - 1, maximizing_player, alpha, beta)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break  # poda
        return best
    else:
        worst = float("inf")
        for piece in moves:
            child = state.clone()
            piece_clone = child.get_piece(piece.owner, piece.number)
            ops.apply_move(child, piece_clone)
            val = expectiminimax(child, depth - 1, maximizing_player, alpha, beta)
            if val < worst:
                worst = val
            if worst < beta:
                beta = worst
            if alpha >= beta:
                break  # poda
        return worst


def choose_move(state, depth=3):
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

    # Ordenar movimientos heurísticamente: probar primero los que más prometen
    # (capturas, rosetas, completar). Mejora poda alfa-beta.
    def quick_score(piece):
        s = state.dice_sum
        if piece.state == C.ESPERA:
            new_pos = s
        else:
            new_pos = piece.position + s
        score = 0
        if new_pos == C.META_POS:
            score += 1000  # completar
        else:
            target = C.square_at(piece.owner, new_pos)
            if target is not None:
                if C.is_rosette(target):
                    score += 200
                if state.occupant_at(target) == C.opponent(piece.owner):
                    score += 300  # captura
                score += new_pos  # progreso
        return score

    moves_sorted = sorted(moves, key=quick_score, reverse=True)

    for piece in moves_sorted:
        child = state.clone()
        piece_clone = child.get_piece(piece.owner, piece.number)
        ops.apply_move(child, piece_clone)
        score = expectiminimax(child, depth, me)
        if score > best_score:
            best_score = score
            best_piece = piece

    return best_piece
