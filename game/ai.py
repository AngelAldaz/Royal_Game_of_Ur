"""
IA del oponente — heurística simple por pesos.

Para cada jugada legal calcula un puntaje sumando pesos según qué
consigue (capturar, completar, caer en roseta, etc.) y elige la jugada
con mayor puntaje. No hay árbol de búsqueda ni cálculo de probabilidades.
"""

from . import eeo
from . import rules
from . import engine


# Pesos heurísticos (de más a menos importante)
PESO_COMPLETAR = 1000   # llevar una ficha a meta
PESO_CAPTURAR  = 500    # capturar ficha rival
PESO_ROSETA    = 300    # caer en roseta (turno extra)
PESO_ENTRAR    = 50     # sacar ficha de la reserva
PESO_AVANCE    = 10     # × posición nueva (mientras más avance, mejor)


def choose_move(state):
    """Elige la ficha con mayor puntaje, o None si no hay jugadas."""
    moves = engine.legal_moves(state)
    if not moves:
        return None
    return max(moves, key=lambda F_i: puntaje(state, F_i))


def puntaje(state, F_i):
    """Puntaje heurístico de mover F_i con ΣD actual."""
    s = state.T.ΣD
    new_P = s if F_i.S == eeo.espera else F_i.P + s

    # Completar ficha (llegar a meta) — siempre la mejor jugada
    if new_P == rules.META_POS:
        return PESO_COMPLETAR

    destino = rules.square_at(F_i.J, new_P)
    total = PESO_AVANCE * new_P

    # Capturar ficha rival
    if state.occupant_at(destino) == rules.opponent(F_i.J):
        total += PESO_CAPTURAR

    # Caer en roseta — turno extra
    if rules.is_rosette(destino):
        total += PESO_ROSETA

    # Sacar ficha de la reserva
    if F_i.S == eeo.espera:
        total += PESO_ENTRAR

    return total
