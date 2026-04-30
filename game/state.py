"""
Estado del juego: clase GameState que materializa el vector EEO de 102 componentes
definido en el analisis 3.1.

Vector de estado:
  Ur = (Jugadores) . (Fichas) . (Dados) . (Tablero) . (Casillas)

  Jugadores:  ((R1, M1), (R2, M2))
  Fichas:     ((n_i, J_i, S_i, P_i)) x 8                  (i = 1..8)
  Dados:      (D1, D2, D3, D4)
  Tablero:    (tau, sigma_D)
  Casillas:   ((O_n, U_n, rho_n)) x 20                    (n = 1..20)

Los nombres de atributos en este código replican EXACTAMENTE las variables
del análisis EEO documentado:

    Entidad          Atributo            Variable EEO    Nombre en código
    ---------------- ------------------- --------------- ----------------
    Jugador (J_j)    Fichas en reserva   R_j             GameState.R[j]
    Jugador (J_j)    Fichas en meta      M_j             GameState.M[j]
    Ficha   (F_i)    Número de ficha     n_i             Piece.n
    Ficha   (F_i)    Jugador dueño       J_i             Piece.J
    Ficha   (F_i)    Estado              S_i             Piece.S
    Ficha   (F_i)    Posición en camino  P_i             Piece.P
    Dado    (D_k)    Resultado           D_k             GameState.D[k-1]
    Tablero (T)      Turno activo        tau             GameState.tau
    Tablero (T)      Suma de dados       sigma_D         GameState.sigma_D  (propiedad)
    Casilla (C_n)    Ocupante            O_n             GameState.O[n]
    Casilla (C_n)    Ubicación           U_n             constante = n
    Casilla (C_n)    Roseta              rho_n           constante (ver C.is_rosette)
"""

from . import constants as C


class Piece:
    """Una ficha del juego. Atributos: n, J, S, P (como en la Tabla 1 del EEO)."""

    __slots__ = ("n", "J", "S", "P")

    def __init__(self, n, J):
        self.n = n              # n_i in {1, 2, 3, 4}
        self.J = J              # J_i in {1, 2}  (jugador dueño)
        self.S = C.ESPERA       # S_i in {espera, activa, completada}
        self.P = 0              # P_i in {0..15} -- 0 = fuera de tablero, 15 = transitorio meta

    def clone(self):
        p = Piece(self.n, self.J)
        p.S = self.S
        p.P = self.P
        return p

    def square(self):
        """Casilla física donde está la ficha (1..20) o None si fuera del tablero."""
        if self.S != C.ACTIVA:
            return None
        return C.square_at(self.J, self.P)


class GameState:
    """
    Estado completo del juego, equivalente al vector EEO Ur de 102 componentes.

    Variables EEO directamente accesibles:
      R   : dict {1: R_1, 2: R_2}     fichas en reserva por jugador
      M   : dict {1: M_1, 2: M_2}     fichas en meta por jugador
      F   : list[Piece] de longitud 8 (F_1..F_4 de J1, F_5..F_8 de J2)
      D   : list[int]   de longitud 4 (D_1..D_4) — cada dado 0 o 1
      tau : 1 o 2                     jugador en turno
      O   : dict {1..20: 0|1|2}       ocupante de cada casilla (O_n)

    Variables auxiliares:
      sigma_D     : suma de los 4 dados (propiedad derivada)
      dice_rolled : si los dados ya se lanzaron en este turno
      last_event  : descripción textual del último operador aplicado
      winner      : jugador ganador (None mientras no termina)
    """

    def __init__(self):
        # Jugadores (R_j, M_j)
        self.R = {C.J1: C.FICHAS_POR_JUGADOR, C.J2: C.FICHAS_POR_JUGADOR}
        self.M = {C.J1: 0, C.J2: 0}

        # Fichas (F_i con n_i, J_i, S_i, P_i)
        self.F = []
        for J in (C.J1, C.J2):
            for n in range(1, C.FICHAS_POR_JUGADOR + 1):
                self.F.append(Piece(n, J))

        # Dados (D_1, D_2, D_3, D_4)
        self.D = [0, 0, 0, 0]

        # Tablero (tau, sigma_D)
        self.tau = C.J1

        # Casillas (O_n) — la ubicación U_n y la roseta rho_n son estáticas
        self.O = {n: 0 for n in range(1, 21)}

        # Auxiliares de control de turno
        self.dice_rolled = False
        self.last_event = "Inicio del juego"
        self.winner = None

    # ----- propiedades derivadas EEO -----

    @property
    def sigma_D(self):
        """Σ D — suma de los 4 dados (atributo derivado del Tablero)."""
        return sum(self.D)

    # ----- accessors -----

    def pieces_of(self, player):
        """Devuelve las fichas del jugador dado."""
        return [p for p in self.F if p.J == player]

    def get_piece(self, J, n):
        """Devuelve la ficha (J_i = J, n_i = n)."""
        for p in self.F:
            if p.J == J and p.n == n:
                return p
        return None

    def occupant_at(self, square):
        """O_n: jugador que ocupa la casilla (1 o 2) o 0 si vacía."""
        return self.O.get(square, 0)

    # ----- utilidades -----

    def clone(self):
        new = GameState.__new__(GameState)
        new.R = dict(self.R)
        new.M = dict(self.M)
        new.F = [p.clone() for p in self.F]
        new.D = list(self.D)
        new.tau = self.tau
        new.O = dict(self.O)
        new.dice_rolled = self.dice_rolled
        new.last_event = self.last_event
        new.winner = self.winner
        return new

    def is_terminal(self):
        return self.winner is not None

    # ----- aliases legibles (compatibilidad con código antiguo) -----
    # NOTA: estos aliases están sólo para que los archivos antiguos sigan
    # funcionando si llegan a llamarlos. Los nombres EEO (R, M, D, tau, O, F)
    # son los oficiales.
    @property
    def players_reserva(self): return self.R
    @property
    def players_meta(self): return self.M
    @property
    def pieces(self): return self.F
    @property
    def dice(self): return self.D
    @dice.setter
    def dice(self, v): self.D = v
    @property
    def turn(self): return self.tau
    @turn.setter
    def turn(self, v): self.tau = v
    @property
    def ocupantes(self): return self.O
    @property
    def dice_sum(self): return self.sigma_D
