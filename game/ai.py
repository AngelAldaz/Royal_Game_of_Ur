"""
IA del oponente.

Estrategia: Expectiminimax con profundidad parametrizada (default 3) y
nodos de azar para los dados.

Los nombres de variables siguen la nomenclatura EEO documentada:
  R   -> reservas        M     -> metas
  n   -> número de ficha J     -> jugador dueño
  S   -> estado          P     -> posición en camino
  D_k -> dado k          tau   -> turno activo    sigma_D -> suma de dados
  O_n -> ocupante        rho_n -> roseta
"""

from . import constants as C
from . import operators as ops


# Probabilidad de obtener una suma sigma_D = s al lanzar 4 dados binarios.
# P(s) = C(4,s) / 16  -- distribución binomial B(4, 0.5).
DICE_PROB = {
    0: 1 / 16,
    1: 4 / 16,
    2: 6 / 16,
    3: 4 / 16,
    4: 1 / 16,
}


# --------- evaluación heurística ---------

def evaluate(state, player):
    """Evalúa el estado desde el punto de vista del jugador 'player'."""
    if state.winner == player:
        return 100000
    if state.winner is not None:
        return -100000

    score = 0
    enemy = C.opponent(player)

    # Fichas en meta (M_j): peso máximo
    score += 1200 * state.M[player]
    score -= 1200 * state.M[enemy]

    # Reserva del rival (R del rival): bueno para nosotros (le falta avanzar)
    score += 12 * state.R[enemy]
    score -= 12 * state.R[player]

    # Posición / progreso de fichas activas (P_i)
    for piece in state.F:
        if piece.S != C.ACTIVA:
            continue
        sq = piece.square()
        weight = 1 if piece.J == player else -1
        # avance lineal en el camino, con bono no lineal cerca de meta
        progress = 8 * piece.P + ((piece.P - 8) ** 2 if piece.P >= 8 else 0)
        score += weight * progress
        # bono por estar en zona privada de salida (segura y cerca de meta)
        if piece.P >= 13:
            score += weight * 60
        # bonos por roseta
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
    cuántas sumas de dados (sigma_D) del rival la pueden capturar en su
    próximo turno, ponderado por probabilidad. Hace lo mismo para fichas
    rivales (oportunidades para nosotros).
    """
    score = 0

    for piece in state.F:
        if piece.S != C.ACTIVA:
            continue
        sq = piece.square()
        if not C.is_shared(sq) or sq == C.ROSETA_SEGURA:
            continue

        weight = -1 if piece.J == player else 1  # exposición propia es mala
        # Probabilidad de que el rival capture esta ficha el próximo turno
        threats_prob = 0.0
        threatening = C.opponent(piece.J)
        for s, prob in DICE_PROB.items():
            if s == 0:
                continue
            for rival_piece in state.F:
                if rival_piece.J != threatening:
                    continue
                if rival_piece.S == C.ESPERA:
                    new_P = s
                elif rival_piece.S == C.ACTIVA:
                    new_P = rival_piece.P + s
                else:
                    continue
                if new_P > C.META_POS or new_P == C.META_POS:
                    continue
                if C.square_at(rival_piece.J, new_P) == sq:
                    threats_prob += prob
                    break  # una amenaza por suma es suficiente

        # threats_prob ∈ [0..1], peso 60 al máximo riesgo
        score += weight * int(60 * threats_prob)

    return score


# --------- expectiminimax ---------

def expectiminimax(state, depth, maximizing_player, alpha=float("-inf"), beta=float("inf")):
    """
    Devuelve el valor del estado bajo expectiminimax.
    `maximizing_player` es la perspectiva fija desde la que evaluamos.

    Tipos de nodo:
      - dice_rolled == False  => nodo CHANCE (esperanza sobre las 5 sumas posibles)
      - dice_rolled == True   => nodo de DECISIÓN (MAX o MIN según tau)

    alpha/beta solo se usan en nodos de decisión (no en chance, porque
    podarlos rompería la esperanza).
    """
    if state.is_terminal() or depth == 0:
        return evaluate(state, maximizing_player)

    if not state.dice_rolled:
        # Nodo CHANCE: esperanza ponderada por P(sigma_D = s)
        expected = 0.0
        for s, prob in DICE_PROB.items():
            child = state.clone()
            child.D = [1] * s + [0] * (C.NUM_DADOS - s)
            child.dice_rolled = True
            if s == 0:
                ops.lose_turn(child)
                expected += prob * expectiminimax(child, depth - 1, maximizing_player)
            else:
                expected += prob * expectiminimax(child, depth, maximizing_player)
        return expected

    # Nodo de DECISIÓN
    moves = ops.legal_moves(state)
    if not moves:
        child = state.clone()
        ops.lose_turn(child)
        return expectiminimax(child, depth - 1, maximizing_player)

    if state.tau == maximizing_player:
        best = float("-inf")
        for piece in moves:
            child = state.clone()
            piece_clone = child.get_piece(piece.J, piece.n)
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
            piece_clone = child.get_piece(piece.J, piece.n)
            ops.apply_move(child, piece_clone)
            val = expectiminimax(child, depth - 1, maximizing_player, alpha, beta)
            if val < worst:
                worst = val
            if worst < beta:
                beta = worst
            if alpha >= beta:
                break
        return worst


def choose_move(state, depth=3):
    """
    Elige la mejor ficha (F_i) a mover para el jugador en turno (tau)
    usando expectiminimax. Retorna la Piece a mover, o None si no hay jugadas.
    """
    moves = ops.legal_moves(state)
    if not moves:
        return None

    me = state.tau
    best_score = float("-inf")
    best_piece = moves[0]

    # Ordenar movimientos heurísticamente para mejorar la poda alfa-beta:
    # primero los más prometedores (capturas, rosetas, completar).
    def quick_score(piece):
        s = state.sigma_D
        if piece.S == C.ESPERA:
            new_P = s
        else:
            new_P = piece.P + s
        score = 0
        if new_P == C.META_POS:
            score += 1000  # Operador "Completar ficha"
        else:
            target = C.square_at(piece.J, new_P)
            if target is not None:
                if C.is_rosette(target):
                    score += 200  # Operador "Turno extra"
                if state.occupant_at(target) == C.opponent(piece.J):
                    score += 300  # Operador "Capturar"
                score += new_P
        return score

    moves_sorted = sorted(moves, key=quick_score, reverse=True)

    for piece in moves_sorted:
        child = state.clone()
        piece_clone = child.get_piece(piece.J, piece.n)
        ops.apply_move(child, piece_clone)
        score = expectiminimax(child, depth, me)
        if score > best_score:
            best_score = score
            best_piece = piece

    return best_piece
