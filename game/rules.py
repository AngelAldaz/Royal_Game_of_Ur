"""
Reglas y helpers derivados (NO están en las Tablas 1 y 2).
"""

from . import eeo


# Camino:  índice = P_i (0..14),  valor = U_n (1..20)
PATH_J_1 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
PATH_J_2 = [0, 15, 16, 17, 18, 5, 6, 7, 8, 9, 10, 11, 12, 19, 20]

# Posición transitoria P_i = 15: la ficha sale del tablero a meta
META_POS = 15

# Zonas
CASILLAS_COMPARTIDAS = {5, 6, 7, 8, 9, 10, 11, 12}
CASILLAS_PRIVADAS_J_1 = {1, 2, 3, 4, 13, 14}
CASILLAS_PRIVADAS_J_2 = {15, 16, 17, 18, 19, 20}

# Regla principal #4: la roseta 8 es inmune a captura
ROSETA_SEGURA = 8


def path_for(J):
    return PATH_J_1 if J == eeo.J_1 else PATH_J_2


def square_at(J, P):
    """U_n donde queda una ficha de J con posición P_i = P."""
    if P == 0 or P == META_POS:
        return None
    return path_for(J)[P]


def square_of(F_i):
    """U_n donde está actualmente F_i (None si no es activa)."""
    if F_i.S != eeo.activa:
        return None
    return square_at(F_i.J, F_i.P)


def is_rosette(U):
    return U in eeo.ROSETAS


def is_shared(U):
    return U in CASILLAS_COMPARTIDAS


def opponent(J):
    """J_opuesto"""
    return eeo.J_2 if J == eeo.J_1 else eeo.J_1
