"""
EEO — Tablas 1 y 2 del análisis EEO 3.1
=========================================

Mapeo 1:1 con el documento 'EEO - The Royal Game of Ur 3-1.md':
los nombres de variables y de operadores en este archivo coinciden
EXACTAMENTE con los de las tablas (incluyendo τ, ΣD, ρ).

══════════════════════════════════════════════════════════════════════
TABLA 1 — ENTIDADES, ATRIBUTOS, VARIABLES Y ESTADOS
══════════════════════════════════════════════════════════════════════

  Entidad                       Atributo            Variable   Estados
  ----------------------------  ------------------  --------   ------------------------------------
  Jugador  (J_j, j ∈ {1,2})     Fichas en reserva   R_j        {0, 1, 2, 3, 4}
                                Fichas en meta      M_j        {0, 1, 2, 3, 4}
  Ficha    (F_i, i ∈ {1..8})    Número de ficha     n_i        {1, 2, 3, 4}
                                Jugador dueño       J_i        {J_1, J_2}
                                Estado              S_i        {espera, activa, completada}
                                Posición en camino  P_i        {0, 1, 2, ..., 20}
  Dado     (D_k, k ∈ {1..4})    Resultado           D_k        {0, 1}
  Tablero  (T)                  Turno activo        τ          {-, J_1, J_2}
                                Suma de dados       ΣD         {0, 1, 2, 3, 4}
  Casilla  (C_n, n ∈ {1..20})   Ocupante            O_n        {vacío, J_1, J_2}
                                Ubicación           U_n        {1, 2, 3, ..., 20}
                                Roseta              ρ_n        {sí, no}

Variable de la Tabla 1   ↔   Acceso en código:

    R_j    ->  GameState.R[j]              j ∈ {J_1, J_2}
    M_j    ->  GameState.M[j]
    n_i    ->  GameState.F[i].n            i ∈ {1..8}
    J_i    ->  GameState.F[i].J
    S_i    ->  GameState.F[i].S
    P_i    ->  GameState.F[i].P
    D_k    ->  GameState.D[k]              k ∈ {1..4}
    τ      ->  GameState.τ
    ΣD     ->  GameState.ΣD                (propiedad: Σ_k D[k])
    O_n    ->  GameState.C[n].O            n ∈ {1..20}
    U_n    ->  GameState.C[n].U
    ρ_n    ->  GameState.C[n].ρ

══════════════════════════════════════════════════════════════════════
TABLA 2 — OPERADORES (1:1 con las filas del análisis)
══════════════════════════════════════════════════════════════════════

    Nº  Operador (Tabla 2)        Función Python
    --  ------------------------  ----------------------------------------
    1   Lanzar dados              lanzar_dados(state)
    2   Entrar ficha al tablero   entrar_ficha_al_tablero(state, piece, target)
    3   Mover ficha               mover_ficha(state, piece, origin, target)
    4   Completar ficha           completar_ficha(state, piece, origin)
    5   Capturar ficha rival      capturar_ficha_rival(state, rival)
    6   Obtener turno extra       obtener_turno_extra(state)
    7   Cambiar turno             cambiar_turno(state)
    8   Perder turno              perder_turno(state)

La condición y el efecto de cada operador están en el docstring de la
función, palabra por palabra del análisis.
"""

import random


# ══════════════════════════════════════════════════════════════════════
# DOMINIOS DE LA TABLA 1
# ══════════════════════════════════════════════════════════════════════

# Identificadores de jugador  (dominio de J_i y de τ)
J_1 = 1
J_2 = 2

# Dominio de S_i  (atributo "Estado" de la Ficha)
ESPERA = "espera"
ACTIVA = "activa"
COMPLETADA = "completada"

# Valores de n para los cuales ρ_n = sí
ROSETAS = {4, 8, 14, 18, 20}

# Cardinalidades de las entidades
FICHAS_POR_JUGADOR = 4   # n_i ∈ {1..4}
NUM_DADOS = 4            # k ∈ {1..4}
NUM_CASILLAS = 20        # n ∈ {1..20}


# ══════════════════════════════════════════════════════════════════════
# ENTIDADES DE LA TABLA 1
# ══════════════════════════════════════════════════════════════════════

class Casilla:
    """
    Entidad C_n.

        O_n  ->  Casilla.O   ocupante   ∈ {0(vacío), J_1, J_2}
        U_n  ->  Casilla.U   ubicación  ∈ {1..20}   (estática, U_n = n)
        ρ_n  ->  Casilla.ρ   roseta     ∈ {sí, no}  (estática)
    """
    __slots__ = ("O", "U", "ρ")

    def __init__(self, n):
        self.O = 0
        self.U = n
        self.ρ = (n in ROSETAS)

    def clone(self):
        c = Casilla.__new__(Casilla)
        c.O = self.O
        c.U = self.U
        c.ρ = self.ρ
        return c


class Piece:
    """
    Entidad F_i.

        n_i  ->  Piece.n   número de ficha   ∈ {1..4}
        J_i  ->  Piece.J   jugador dueño     ∈ {J_1, J_2}
        S_i  ->  Piece.S   estado            ∈ {espera, activa, completada}
        P_i  ->  Piece.P   posición camino   ∈ {0..14}
    """
    __slots__ = ("n", "J", "S", "P")

    def __init__(self, n, J):
        self.n = n
        self.J = J
        self.S = ESPERA
        self.P = 0

    def clone(self):
        p = Piece(self.n, self.J)
        p.S = self.S
        p.P = self.P
        return p


class GameState:
    """
    Vector EEO Ur — sólo las variables de la Tabla 1, nada más.

        R[j]     ->  R_j     j ∈ {J_1, J_2}
        M[j]     ->  M_j
        F[i]     ->  F_i     i ∈ {1..8}  (F_1..F_4 de J_1, F_5..F_8 de J_2)
        D[k]     ->  D_k     k ∈ {1..4}
        τ        ->  τ
        ΣD       ->  ΣD      (propiedad)
        C[n]     ->  C_n     n ∈ {1..20}
    """

    __slots__ = ("R", "M", "F", "D", "τ", "C")

    def __init__(self):
        # Jugadores  -- R_j, M_j
        self.R = {J_1: FICHAS_POR_JUGADOR, J_2: FICHAS_POR_JUGADOR}
        self.M = {J_1: 0, J_2: 0}

        # Fichas  -- F_1..F_8  (n_i, J_i, S_i, P_i)
        self.F = {}
        i = 1
        for J in (J_1, J_2):
            for n in range(1, FICHAS_POR_JUGADOR + 1):
                self.F[i] = Piece(n, J)
                i += 1

        # Dados  -- D_1..D_4
        self.D = {k: 0 for k in range(1, NUM_DADOS + 1)}

        # Tablero  -- τ  (ΣD es derivado)
        self.τ = J_1

        # Casillas  -- C_1..C_20  (O_n, U_n, ρ_n)
        self.C = {n: Casilla(n) for n in range(1, NUM_CASILLAS + 1)}

    @property
    def ΣD(self):
        """ΣD = D_1 + D_2 + D_3 + D_4"""
        return sum(self.D.values())


# ══════════════════════════════════════════════════════════════════════
# TABLA 2 — OPERADORES (1:1 con las filas del análisis)
# ══════════════════════════════════════════════════════════════════════

def lanzar_dados(state, rng=None):
    """
    Operador 1 — Lanzar dados.

        Condición:  Si τ = J_j
        Efecto:     entonces D_k = {0, 1}  para k = 1..4
                              ΣD = D_1 + D_2 + D_3 + D_4
    """
    rng = rng or random
    for k in range(1, NUM_DADOS + 1):
        state.D[k] = rng.randint(0, 1)


def entrar_ficha_al_tablero(state, piece, target):
    """
    Operador 2 — Entrar ficha al tablero.

        Condición:  Si R_j > 0  ∧  ΣD > 0  ∧  O_destino ≠ J_j
        Efecto:     entonces S_i = activa
                              P_i = ΣD
                              O_destino = J_j
                              R_j = R_j − 1
    """
    piece.S = ACTIVA
    piece.P = state.ΣD
    state.C[target].O = piece.J
    state.R[piece.J] -= 1


def mover_ficha(state, piece, origin, target):
    """
    Operador 3 — Mover ficha.

        Condición:  Si S_i = activa  ∧  ΣD > 0  ∧  P_i + ΣD ≤ 14
                       ∧  O_destino ≠ J_j
                       ∧  ¬(O_destino = J_rival  ∧  ρ_destino = SI)
        Efecto:     entonces O_origen = vacío
                              P_i = P_i + ΣD
                              O_destino = J_j
    """
    state.C[origin].O = 0
    piece.P += state.ΣD
    state.C[target].O = piece.J


def completar_ficha(state, piece, origin):
    """
    Operador 4 — Completar ficha.

        Condición:  Si S_i = activa  ∧  P_i + ΣD = 15
        Efecto:     entonces S_i = completada
                              P_i = 0
                              M_j = M_j + 1
                              O_origen = vacío
    """
    state.C[origin].O = 0
    piece.S = COMPLETADA
    piece.P = 0
    state.M[piece.J] += 1


def capturar_ficha_rival(state, rival):
    """
    Operador 5 — Capturar ficha rival.

        Condición:  Si O_destino = J_rival
                       ∧  U_destino ∈ {5..12}
                       ∧  ρ_destino = NO
        Efecto:     entonces S_rival = espera
                              P_rival = 0
                              R_rival = R_rival + 1
    """
    rival.S = ESPERA
    rival.P = 0
    state.R[rival.J] += 1


def obtener_turno_extra(state):
    """
    Operador 6 — Obtener turno extra.

        Condición:  Si ρ_destino = SI
        Efecto:     entonces τ = J_j   (se mantiene)
    """
    # τ no cambia: el mismo jugador conserva el turno.
    pass


def cambiar_turno(state):
    """
    Operador 7 — Cambiar turno.

        Condición:  Si ρ_destino = NO
        Efecto:     entonces τ = J_opuesto
    """
    state.τ = J_2 if state.τ == J_1 else J_1


def perder_turno(state):
    """
    Operador 8 — Perder turno.

        Condición:  Si ΣD = 0
        Efecto:     entonces τ = J_opuesto
    """
    state.τ = J_2 if state.τ == J_1 else J_1
