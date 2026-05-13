"""
IA del oponente.

Estrategia: Expectiminimax con profundidad parametrizada (default 3) y
nodos de azar para los dados.

Usa:
  - eeo.py    : dominios (J_1, J_2, ESPERA, ACTIVA, NUM_DADOS).
  - rules.py  : helpers geográficos (square_at, square_of, is_rosette,
                is_shared, opponent, ROSETA_SEGURA, META_POS).
  - engine.py : motor de juego (perder_turno, apply_move, legal_moves).
"""

from . import eeo
from . import rules
from . import engine


# Probabilidad de obtener una suma ΣD = s al lanzar 4 dados binarios.
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
    enemy = rules.opponent(player)

    # Fichas en meta (M_j): peso máximo
    score += 1200 * state.M[player]
    score -= 1200 * state.M[enemy]

    # Reserva del rival (R del rival): bueno para nosotros (le falta avanzar)
    score += 12 * state.R[enemy]
    score -= 12 * state.R[player]

    # Posición / progreso de fichas activas (P_i)
    for piece in state.F.values():
        if piece.S != eeo.ACTIVA:
            continue
        sq = rules.square_of(piece)
        weight = 1 if piece.J == player else -1
        # avance lineal en el camino, con bono no lineal cerca de meta
        progress = 8 * piece.P + ((piece.P - 8) ** 2 if piece.P >= 8 else 0)
        score += weight * progress
        # bono por estar en zona privada de salida (segura y cerca de meta)
        if piece.P >= 13:
            score += weight * 60
        # bonos por roseta
        if sq == rules.ROSETA_SEGURA:
            score += weight * 50  # roseta + segura
        elif rules.is_rosette(sq):
            score += weight * 35

    # Análisis dinámico de amenazas y oportunidades en zona compartida
    score += _threat_score(state, player)

    return score


def _threat_score(state, player):
    """
    Para cada ficha propia activa en zona compartida (no segura), calcula
    cuántas sumas de dados (ΣD) del rival la pueden capturar en su próximo
    turno, ponderado por probabilidad. Hace lo mismo para fichas rivales
    (oportunidades para nosotros).
    """
    score = 0

    for piece in state.F.values():
        if piece.S != eeo.ACTIVA:
            continue
        sq = rules.square_of(piece)
        if not rules.is_shared(sq) or sq == rules.ROSETA_SEGURA:
            continue

        weight = -1 if piece.J == player else 1  # exposición propia es mala
        # Probabilidad de que el rival capture esta ficha el próximo turno
        threats_prob = 0.0
        threatening = rules.opponent(piece.J)
        for s, prob in DICE_PROB.items():
            if s == 0:
                continue
            for rival_piece in state.F.values():
                if rival_piece.J != threatening:
                    continue
                if rival_piece.S == eeo.ESPERA:
                    new_P = s
                elif rival_piece.S == eeo.ACTIVA:
                    new_P = rival_piece.P + s
                else:
                    continue
                if new_P > rules.META_POS or new_P == rules.META_POS:
                    continue
                if rules.square_at(rival_piece.J, new_P) == sq:
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
      - dice_rolled == True   => nodo de DECISIÓN (MAX o MIN según τ)

    alpha/beta solo se usan en nodos de decisión (no en chance, porque
    podarlos rompería la esperanza).
    """
    if state.is_terminal() or depth == 0:
        return evaluate(state, maximizing_player)

    if not state.dice_rolled:
        # Nodo CHANCE: esperanza ponderada por P(ΣD = s)
        expected = 0.0
        for s, prob in DICE_PROB.items():
            child = state.clone()
            for k in range(1, eeo.NUM_DADOS + 1):
                child.D[k] = 1 if k <= s else 0
            child.dice_rolled = True
            if s == 0:
                engine.perder_turno(child)
                expected += prob * expectiminimax(child, depth - 1, maximizing_player)
            else:
                expected += prob * expectiminimax(child, depth, maximizing_player)
        return expected

    # Nodo de DECISIÓN
    moves = engine.legal_moves(state)
    if not moves:
        child = state.clone()
        engine.perder_turno(child)
        return expectiminimax(child, depth - 1, maximizing_player)

    if state.τ == maximizing_player:
        best = float("-inf")
        for piece in moves:
            child = state.clone()
            piece_clone = child.get_piece(piece.J, piece.n)
            engine.apply_move(child, piece_clone)
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
            engine.apply_move(child, piece_clone)
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
    Elige la mejor ficha (F_i) a mover para el jugador en turno (τ)
    usando expectiminimax. Retorna la Piece a mover, o None si no hay jugadas.
    """
    moves = engine.legal_moves(state)
    if not moves:
        return None

    me = state.τ
    best_score = float("-inf")
    best_piece = moves[0]

    # Ordenar movimientos heurísticamente para mejorar la poda alfa-beta:
    # primero los más prometedores (capturas, rosetas, completar).
    def quick_score(piece):
        s = state.ΣD
        if piece.S == eeo.ESPERA:
            new_P = s
        else:
            new_P = piece.P + s
        score = 0
        if new_P == rules.META_POS:
            score += 1000  # Operador 4 "Completar ficha"
        else:
            target = rules.square_at(piece.J, new_P)
            if target is not None:
                if rules.is_rosette(target):
                    score += 200  # Operador 6 "Turno extra"
                if state.occupant_at(target) == rules.opponent(piece.J):
                    score += 300  # Operador 5 "Capturar"
                score += new_P
        return score

    moves_sorted = sorted(moves, key=quick_score, reverse=True)

    for piece in moves_sorted:
        child = state.clone()
        piece_clone = child.get_piece(piece.J, piece.n)
        engine.apply_move(child, piece_clone)
        score = expectiminimax(child, depth, me)
        if score > best_score:
            best_score = score
            best_piece = piece

    return best_piece
