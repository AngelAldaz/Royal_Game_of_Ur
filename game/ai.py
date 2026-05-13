"""
IA del oponente — Expectiminimax con poda alfa-beta y nodos de azar
para los 4 dados.
"""

from . import eeo
from . import rules
from . import engine


# P(ΣD = s) con 4 dados binarios — binomial B(4, 0.5).
DICE_PROB = {0: 1/16, 1: 4/16, 2: 6/16, 3: 4/16, 4: 1/16}


def evaluate(state, player):
    """Evalúa el estado desde el punto de vista del jugador `player`."""
    if state.winner == player:
        return 100000
    if state.winner is not None:
        return -100000

    score = 0
    enemy = rules.opponent(player)

    score += 1200 * state.J[player].M
    score -= 1200 * state.J[enemy].M
    score += 12 * state.J[enemy].R
    score -= 12 * state.J[player].R

    for F_i in state.F.values():
        if F_i.S != eeo.activa:
            continue
        U = rules.square_of(F_i)
        weight = 1 if F_i.J == player else -1
        progress = 8 * F_i.P + ((F_i.P - 8) ** 2 if F_i.P >= 8 else 0)
        score += weight * progress
        if F_i.P >= 13:
            score += weight * 60
        if U == rules.ROSETA_SEGURA:
            score += weight * 50
        elif rules.is_rosette(U):
            score += weight * 35

    score += _threat_score(state, player)
    return score


def _threat_score(state, player):
    """Probabilidad de captura por el rival sobre fichas en zona compartida."""
    score = 0
    for F_i in state.F.values():
        if F_i.S != eeo.activa:
            continue
        U = rules.square_of(F_i)
        if not rules.is_shared(U) or U == rules.ROSETA_SEGURA:
            continue

        weight = -1 if F_i.J == player else 1
        threats_prob = 0.0
        threatening = rules.opponent(F_i.J)
        for s, prob in DICE_PROB.items():
            if s == 0:
                continue
            for F_rival in state.F.values():
                if F_rival.J != threatening:
                    continue
                if F_rival.S == eeo.espera:
                    new_P = s
                elif F_rival.S == eeo.activa:
                    new_P = F_rival.P + s
                else:
                    continue
                if new_P >= rules.META_POS:
                    continue
                if rules.square_at(F_rival.J, new_P) == U:
                    threats_prob += prob
                    break

        score += weight * int(60 * threats_prob)
    return score


def expectiminimax(state, depth, maximizing_player, alpha=float("-inf"), beta=float("inf")):
    """
    Nodo CHANCE  → esperanza sobre las 5 sumas posibles (no se poda).
    Nodo MAX/MIN → según τ; alfa-beta sólo aquí.
    """
    if state.is_terminal() or depth == 0:
        return evaluate(state, maximizing_player)

    if not state.dice_rolled:
        expected = 0.0
        for s, prob in DICE_PROB.items():
            child = state.clone()
            for k in range(1, 5):
                child.D[k].D = 1 if k <= s else 0
            child.T.ΣD = s
            child.dice_rolled = True
            if s == 0:
                engine.perder_turno(child)
                expected += prob * expectiminimax(child, depth - 1, maximizing_player)
            else:
                expected += prob * expectiminimax(child, depth, maximizing_player)
        return expected

    moves = engine.legal_moves(state)
    if not moves:
        child = state.clone()
        engine.perder_turno(child)
        return expectiminimax(child, depth - 1, maximizing_player)

    if state.T.τ == maximizing_player:
        best = float("-inf")
        for F_i in moves:
            child = state.clone()
            F_i_clone = child.get_piece(F_i.J, F_i.n)
            engine.apply_move(child, F_i_clone)
            val = expectiminimax(child, depth - 1, maximizing_player, alpha, beta)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best
    else:
        worst = float("inf")
        for F_i in moves:
            child = state.clone()
            F_i_clone = child.get_piece(F_i.J, F_i.n)
            engine.apply_move(child, F_i_clone)
            val = expectiminimax(child, depth - 1, maximizing_player, alpha, beta)
            if val < worst:
                worst = val
            if worst < beta:
                beta = worst
            if alpha >= beta:
                break
        return worst


def choose_move(state, depth=3):
    """Elige la mejor F_i para τ usando expectiminimax."""
    moves = engine.legal_moves(state)
    if not moves:
        return None

    me = state.T.τ
    best_score = float("-inf")
    best_F_i = moves[0]

    def quick_score(F_i):
        s = state.T.ΣD
        new_P = s if F_i.S == eeo.espera else F_i.P + s
        score = 0
        if new_P == rules.META_POS:
            score += 1000
        else:
            destino = rules.square_at(F_i.J, new_P)
            if destino is not None:
                if rules.is_rosette(destino):
                    score += 200
                if state.occupant_at(destino) == rules.opponent(F_i.J):
                    score += 300
                score += new_P
        return score

    for F_i in sorted(moves, key=quick_score, reverse=True):
        child = state.clone()
        F_i_clone = child.get_piece(F_i.J, F_i.n)
        engine.apply_move(child, F_i_clone)
        score = expectiminimax(child, depth, me)
        if score > best_score:
            best_score = score
            best_F_i = F_i

    return best_F_i
