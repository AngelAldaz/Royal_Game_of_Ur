"""
Constantes del juego Royal Game of Ur.
Mapeo entre posiciones del camino (1..14) y casillas físicas del tablero (1..20),
listas estáticas de rosetas y zonas, etc.

Esto refleja la Tabla 1 del análisis EEO 3.1.
"""

# Identificadores de jugador
J1 = 1
J2 = 2

# Estados de una ficha
ESPERA = "espera"
ACTIVA = "activa"
COMPLETADA = "completada"

# Casillas roseta (atributo rho_n = SI)
ROSETAS = {4, 8, 14, 18, 20}

# Casilla compartida segura (no se puede capturar)
ROSETA_SEGURA = 8

# Casillas compartidas (zona común): posiciones 5..12 del camino
CASILLAS_COMPARTIDAS = {5, 6, 7, 8, 9, 10, 11, 12}

# Casillas privadas de cada jugador
CASILLAS_PRIVADAS_J1 = {1, 2, 3, 4, 13, 14}
CASILLAS_PRIVADAS_J2 = {15, 16, 17, 18, 19, 20}

# Camino que sigue cada jugador: indice = posicion en camino (1..14), valor = casilla fisica
# El indice 0 representa "fuera del tablero" (en reserva o ya completada)
PATH_J1 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
PATH_J2 = [0, 15, 16, 17, 18, 5, 6, 7, 8, 9, 10, 11, 12, 19, 20]

# Posicion 15 en el camino significa "salida a meta" (no es una casilla fisica)
META_POS = 15

# Numero de fichas por jugador
FICHAS_POR_JUGADOR = 4

# Numero de dados
NUM_DADOS = 4


def path_for(player):
    """Devuelve el camino del jugador."""
    return PATH_J1 if player == J1 else PATH_J2


def square_at(player, position):
    """
    Devuelve la casilla fisica donde estaria una ficha del jugador en la posicion del camino.
    Si position == 0 -> ficha fuera del tablero (reserva o meta).
    Si position == META_POS (15) -> ficha completada.
    """
    if position == 0:
        return None
    if position == META_POS:
        return None
    return path_for(player)[position]


def is_rosette(square):
    """True si la casilla es roseta."""
    return square in ROSETAS


def is_shared(square):
    """True si la casilla es compartida (zona comun)."""
    return square in CASILLAS_COMPARTIDAS


def opponent(player):
    return J2 if player == J1 else J1
