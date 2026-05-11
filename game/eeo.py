"""
EEO — Tablas 1 y 2 del análisis EEO 3.1
=========================================

ESTE ARCHIVO CONTIENE EXCLUSIVAMENTE LO QUE APARECE EN LAS
TABLAS 1 Y 2 DEL DOCUMENTO 'EEO - The Royal Game of Ur 3-1.md'.

  - Dominios (estados) de cada variable de la Tabla 1.
  - Entidades de la Tabla 1 como clases (Casilla, Piece, GameState),
    con los atributos exactos: O, U, ρ / n, J, S, P / R, M, F, D, τ, ΣD, C.
  - Los 8 operadores de la Tabla 2 como funciones en el orden y con el
    nombre exacto que aparecen en el documento.

Cualquier otra cosa (paths, zonas, roseta segura, helpers, orquestador
apply_move, consultas legal_moves, control de turno con dice_rolled,
last_event y winner) NO está en este archivo: vive en
  - game/rules.py   — reglas derivadas y helpers.
  - game/engine.py  — Game (estado de sesión) + apply_move + legal_moves.

══════════════════════════════════════════════════════════════════════
TABLA 1 — ENTIDADES, ATRIBUTOS, VARIABLES Y ESTADOS (dominios)
══════════════════════════════════════════════════════════════════════

  Entidad                            Atributo            Variable   Estados (valores posibles)
  ---------------------------------  ------------------  --------   ----------------------------------
  Jugador  (J_j, j ∈ {1,2})          Fichas en reserva   R_j        {0, 1, 2, 3, 4}
                                     Fichas en meta      M_j        {0, 1, 2, 3, 4}
  Ficha    (F_i, i ∈ {1..8})         Número de ficha     n_i        {1, 2, 3, 4}
                                     Jugador dueño       J_i        {J_1, J_2}
                                     Estado              S_i        {espera, activa, completada}
                                     Posición en camino  P_i        {0, 1, 2, ..., 20}   (0 = fuera)
  Dado     (D_k, k ∈ {1..4})         Resultado           D_k        {0, 1}
  Tablero  (T)                       Turno activo        τ          {-, J_1, J_2}
                                     Suma de dados       ΣD         {0, 1, 2, 3, 4}   (= Σ_{k=1..4} D_k)
  Casilla  (C_n, n ∈ {1..20})        Ocupante            O_n        {vacío, J_1, J_2}
                                     Ubicación           U_n        {1, 2, 3, ..., 20}
                                     Roseta              ρ_n        {sí, no}

Notas literales de la Tabla 1:
  * n_i y J_i son estáticos: identifican unívocamente cada ficha.
  * Casillas privadas restringen su ocupante:
        O_n ∈ {vacío, J_1} para casillas de J_1,
        O_n ∈ {vacío, J_2} para casillas de J_2.
  * U_n y ρ_n son estáticos: U_n = n; ρ_n = sí sólo para n ∈ {4, 8, 14, 18, 20}.

Mapeo Variable ↔ Código (una sola ubicación por variable):

    R_j      ->  GameState.R[j]              j ∈ {J1, J2}
    M_j      ->  GameState.M[j]
    n_i      ->  Piece.n
    J_i      ->  Piece.J
    S_i      ->  Piece.S
    P_i      ->  Piece.P
    D_k      ->  GameState.D[k-1]            k ∈ {1..4}
    τ        ->  GameState.tau
    ΣD       ->  GameState.sigma_D           (propiedad derivada)
    O_n      ->  GameState.C[n].O            n ∈ {1..20}
    U_n      ->  GameState.C[n].U            (estática, U_n = n)
    ρ_n      ->  GameState.C[n].rho          (estática, sí ↔ n ∈ ROSETAS)

══════════════════════════════════════════════════════════════════════
TABLA 2 — OPERADORES Y REGLAS DEL JUEGO (1 operador = 1 función)
══════════════════════════════════════════════════════════════════════

    Nº  Operador                     Función Python
    --  ---------------------------  ----------------------------
    1   Lanzar dados                 lanzar_dados(state)
    2   Entrar ficha al tablero      entrar_ficha(state, piece, target)
    3   Mover ficha                  mover_ficha(state, piece, origin, target)
    4   Completar ficha              completar_ficha(state, piece, origin)
    5   Capturar ficha rival         capturar_ficha(state, rival)
    6   Obtener turno extra          obtener_turno_extra(state)
    7   Cambiar turno                cambiar_turno(state)
    8   Perder turno                 perder_turno(state)

El número de cada función corresponde al orden de aparición en la Tabla 2.
La condición y el efecto de cada operador están en el docstring de la
función, palabra por palabra del análisis.
"""

import random


# ══════════════════════════════════════════════════════════════════════
# DOMINIOS DE LA TABLA 1 (estados / valores posibles)
# ══════════════════════════════════════════════════════════════════════

# Identificadores de jugador  (dominio de J_i y de τ)
J1 = 1
J2 = 2

# Dominio de S_i  ("Estado" de la Ficha)
ESPERA = "espera"
ACTIVA = "activa"
COMPLETADA = "completada"

# Valores de n para los que ρ_n = sí  (nota de la Tabla 1)
ROSETAS = {4, 8, 14, 18, 20}

# Cardinalidades de las entidades de la Tabla 1
FICHAS_POR_JUGADOR = 4   # n_i ∈ {1..4}
NUM_DADOS = 4            # k ∈ {1..4}
NUM_CASILLAS = 20        # n ∈ {1..20}


# ══════════════════════════════════════════════════════════════════════
# ENTIDADES DE LA TABLA 1
# ══════════════════════════════════════════════════════════════════════

class Casilla:
    """
    Entidad C_n.

        O_n   ->  Casilla.O    ocupante   ∈ {0(vacío), J1, J2}
        U_n   ->  Casilla.U    ubicación física   ∈ {1..20}   (estática)
        ρ_n   ->  Casilla.rho  roseta             ∈ {sí, no}  (estática)
    """
    __slots__ = ("O", "U", "rho")

    def __init__(self, n):
        self.O = 0
        self.U = n
        self.rho = (n in ROSETAS)

    def clone(self):
        c = Casilla.__new__(Casilla)
        c.O = self.O
        c.U = self.U
        c.rho = self.rho
        return c


class Piece:
    """
    Entidad F_i.

        n_i  ->  Piece.n   número de ficha   ∈ {1..4}
        J_i  ->  Piece.J   jugador dueño     ∈ {J1, J2}
        S_i  ->  Piece.S   estado            ∈ {espera, activa, completada}
        P_i  ->  Piece.P   posición camino   ∈ {0..14}     (0 = fuera)
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
    Vector EEO Ur — entidades de la Tabla 1 íntegras y nada más.

        R[j]      ->  R_j         (j ∈ {J1, J2})
        M[j]      ->  M_j
        F[i-1]    ->  F_i         (i ∈ 1..8 : F_1..F_4 de J1, F_5..F_8 de J2)
        D[k-1]    ->  D_k         (k ∈ 1..4)
        tau       ->  τ           jugador en turno
        sigma_D   ->  ΣD          ΣD_k (propiedad derivada)
        C[n]      ->  C_n         (n ∈ 1..20)  -- expone O, U, ρ

    Dimensión del vector: 4 + 32 + 4 + 2 + 60 = 102 componentes.
    """

    __slots__ = ("R", "M", "F", "D", "tau", "C")

    def __init__(self):
        # Jugadores  -- R_j, M_j
        self.R = {J1: FICHAS_POR_JUGADOR, J2: FICHAS_POR_JUGADOR}
        self.M = {J1: 0, J2: 0}

        # Fichas  -- F_1..F_8  (n_i, J_i, S_i, P_i)
        self.F = []
        for J in (J1, J2):
            for n in range(1, FICHAS_POR_JUGADOR + 1):
                self.F.append(Piece(n, J))

        # Dados  -- D_1..D_4
        self.D = [0] * NUM_DADOS

        # Tablero  -- τ (ΣD es derivado)
        self.tau = J1

        # Casillas  -- C_1..C_20  (O_n, U_n, ρ_n)
        self.C = {n: Casilla(n) for n in range(1, NUM_CASILLAS + 1)}

    @property
    def sigma_D(self):
        """ΣD = D_1 + D_2 + D_3 + D_4"""
        return sum(self.D)


# ══════════════════════════════════════════════════════════════════════
# TABLA 2 — OPERADORES (uno por función, en el orden del análisis)
# ══════════════════════════════════════════════════════════════════════

def lanzar_dados(state, rng=None):
    """
    Operador 1 — Lanzar dados.

        Condición:   Si τ = J_j
        Efecto:      entonces D_k ∈ {0, 1}  para k = 1..4
                              ΣD = D_1 + D_2 + D_3 + D_4
    """
    rng = rng or random
    state.D = [rng.randint(0, 1) for _ in range(NUM_DADOS)]


def entrar_ficha(state, piece, target):
    """
    Operador 2 — Entrar ficha al tablero.

        Condición:   Si R_j > 0  ∧  ΣD > 0  ∧  O_destino ≠ J_j
        Efecto:      entonces S_i = activa
                              P_i = ΣD
                              O_destino = J_j
                              R_j = R_j − 1
    """
    piece.S = ACTIVA
    piece.P = state.sigma_D
    state.C[target].O = piece.J
    state.R[piece.J] -= 1


def mover_ficha(state, piece, origin, target):
    """
    Operador 3 — Mover ficha.

        Condición:   Si S_i = activa  ∧  ΣD > 0  ∧  P_i + ΣD ≤ 14
                        ∧  O_destino ≠ J_j
                        ∧  ¬(O_destino = J_rival  ∧  ρ_destino = sí)
        Efecto:      entonces O_origen = vacío
                              P_i = P_i + ΣD
                              O_destino = J_j
    """
    state.C[origin].O = 0
    piece.P += state.sigma_D
    state.C[target].O = piece.J


def completar_ficha(state, piece, origin):
    """
    Operador 4 — Completar ficha.

        Condición:   Si S_i = activa  ∧  P_i + ΣD = 15
        Efecto:      entonces S_i = completada
                              P_i = 0
                              M_j = M_j + 1
                              O_origen = vacío
    """
    state.C[origin].O = 0
    piece.S = COMPLETADA
    piece.P = 0
    state.M[piece.J] += 1


def capturar_ficha(state, rival):
    """
    Operador 5 — Capturar ficha rival.

        Condición:   Si O_destino = J_rival
                        ∧  U_destino ∈ {5..12}
                        ∧  ρ_destino = no
        Efecto:      entonces S_rival = espera
                              P_rival = 0
                              R_rival = R_rival + 1
    """
    rival.S = ESPERA
    rival.P = 0
    state.R[rival.J] += 1


def obtener_turno_extra(state):
    """
    Operador 6 — Obtener turno extra.

        Condición:   Si ρ_destino = sí
        Efecto:      entonces τ = J_j   (se mantiene)
    """
    # τ no cambia: el mismo jugador conserva el turno.
    pass


def cambiar_turno(state):
    """
    Operador 7 — Cambiar turno.

        Condición:   Si ρ_destino = no
        Efecto:      entonces τ = J_opuesto
    """
    state.tau = J2 if state.tau == J1 else J1


def perder_turno(state):
    """
    Operador 8 — Perder turno.

        Condición:   Si ΣD = 0
        Efecto:      entonces τ = J_opuesto
    """
    state.tau = J2 if state.tau == J1 else J1
