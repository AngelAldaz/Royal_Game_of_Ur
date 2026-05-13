"""
Reglas y helpers derivados (NO están en las Tablas 1 y 2).

Apoyan a `eeo.py` con la topología del tablero:
  - PATH_J_1, PATH_J_2  : camino que sigue cada jugador (P_i → U_n).
  - META_POS            : posición transitoria "salida a meta" (P_i = 15).
  - CASILLAS_*          : zonas del tablero (compartidas / privadas).
  - ROSETA_SEGURA       : la roseta 8 protege de captura (regla principal #4).
  - path_for, square_at, square_of, is_rosette, is_shared, opponent.
"""

from . import eeo


# Camino: índice = P_i (0..14), valor = U_n (1..20)
PATH_J_1 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
PATH_J_2 = [0, 15, 16, 17, 18, 5, 6, 7, 8, 9, 10, 11, 12, 19, 20]

# Valor transitorio de P_i que representa "salida a la meta"
META_POS = 15

# Zonas del tablero (sección 1 del análisis)
CASILLAS_COMPARTIDAS = {5, 6, 7, 8, 9, 10, 11, 12}
CASILLAS_PRIVADAS_J_1 = {1, 2, 3, 4, 13, 14}
CASILLAS_PRIVADAS_J_2 = {15, 16, 17, 18, 19, 20}

# Regla principal #4: la roseta 8 es inmune a captura
ROSETA_SEGURA = 8


def path_for(J):
    """Camino del jugador J (lista indexable por P_i)."""
    return PATH_J_1 if J == eeo.J_1 else PATH_J_2


def square_at(J, P):
    """U_n donde queda una ficha de J con posición P_i = P.
    Retorna None si la ficha está fuera del tablero (P = 0 ó P = META_POS).
    """
    if P == 0 or P == META_POS:
        return None
    return path_for(J)[P]


def square_of(piece):
    """U_n donde está actualmente la ficha (None si no es S_i = activa)."""
    if piece.S != eeo.ACTIVA:
        return None
    return square_at(piece.J, piece.P)


def is_rosette(square):
    """ρ_n = sí  ↔  True"""
    return square in eeo.ROSETAS


def is_shared(square):
    """U_n ∈ {5..12}  ↔  True"""
    return square in CASILLAS_COMPARTIDAS


def opponent(J):
    """J_opuesto"""
    return eeo.J_2 if J == eeo.J_1 else eeo.J_1
