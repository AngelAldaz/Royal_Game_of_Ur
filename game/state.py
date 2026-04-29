"""
Estado del juego: clase GameState que materializa el vector EEO de 102 componentes
definido en el analisis 3.1.

Vector de estado:
  Ur = (Jugadores) . (Fichas) . (Dados) . (Tablero) . (Casillas)

  Jugadores:  ((R1,M1),(R2,M2))
  Fichas:     ((n_i, J_i, S_i, P_i)) x 8
  Dados:      (D1, D2, D3, D4)
  Tablero:    (turno, suma_dados)
  Casillas:   ((O_n, U_n, rho_n)) x 20
"""

import copy
from . import constants as C


class Piece:
    """Una ficha del juego. Atributos: numero, dueño, estado, posicion en el camino."""

    __slots__ = ("number", "owner", "state", "position")

    def __init__(self, number, owner):
        self.number = number          # n_i in {1,2,3,4}
        self.owner = owner            # J_i in {1,2}
        self.state = C.ESPERA         # S_i in {espera, activa, completada}
        self.position = 0             # P_i in {0..15} -- 0 = fuera, 15 = meta (transitorio)

    def clone(self):
        p = Piece(self.number, self.owner)
        p.state = self.state
        p.position = self.position
        return p

    def square(self):
        """Casilla fisica donde está la ficha (1..20) o None si fuera del tablero."""
        if self.state != C.ACTIVA:
            return None
        return C.square_at(self.owner, self.position)


class GameState:
    """
    Estado completo del juego, equivalente al vector EEO.

    Atributos directos:
      players_reserva: dict {1: int, 2: int}  -> R_j
      players_meta:    dict {1: int, 2: int}  -> M_j
      pieces:          list[Piece] de longitud 8 (4 de J1 + 4 de J2)
      dice:            list[int] de longitud 4 (cada uno 0 o 1)
      turn:            1 o 2 (tau)
      ocupantes:       dict {1..20: 0|1|2}  -> O_n (0 = vacio)
    """

    def __init__(self):
        self.players_reserva = {C.J1: C.FICHAS_POR_JUGADOR, C.J2: C.FICHAS_POR_JUGADOR}
        self.players_meta = {C.J1: 0, C.J2: 0}
        self.pieces = []
        for owner in (C.J1, C.J2):
            for n in range(1, C.FICHAS_POR_JUGADOR + 1):
                self.pieces.append(Piece(n, owner))
        self.dice = [0, 0, 0, 0]
        self.turn = C.J1
        self.ocupantes = {n: 0 for n in range(1, 21)}
        self.dice_rolled = False  # indica si en este turno ya se lanzaron los dados
        self.last_event = "Inicio del juego"  # mensaje del ultimo operador aplicado
        self.winner = None

    # ----- propiedades derivadas -----

    @property
    def dice_sum(self):
        """Suma de los 4 dados (Σ D)."""
        return sum(self.dice)

    def pieces_of(self, player):
        return [p for p in self.pieces if p.owner == player]

    def get_piece(self, owner, number):
        for p in self.pieces:
            if p.owner == owner and p.number == number:
                return p
        return None

    # ----- utilidades -----

    def clone(self):
        new = GameState.__new__(GameState)
        new.players_reserva = dict(self.players_reserva)
        new.players_meta = dict(self.players_meta)
        new.pieces = [p.clone() for p in self.pieces]
        new.dice = list(self.dice)
        new.turn = self.turn
        new.ocupantes = dict(self.ocupantes)
        new.dice_rolled = self.dice_rolled
        new.last_event = self.last_event
        new.winner = self.winner
        return new

    def is_terminal(self):
        return self.winner is not None

    def occupant_at(self, square):
        """Devuelve el jugador que ocupa la casilla (1 o 2) o 0 si vacia."""
        return self.ocupantes.get(square, 0)
