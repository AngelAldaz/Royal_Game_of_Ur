"""
EEO 3.1 — Tablas 1 y 2 del análisis del Royal Game of Ur.

Tabla 1 — Entidades, atributos y dominios:
    Jugador  J_j   →  R_j, M_j
    Ficha    F_i   →  n_i, J_i, S_i, P_i
    Dado     D_k   →  D_k
    Tablero  T     →  τ, ΣD
    Casilla  C_n   →  O_n, U_n, ρ_n

Tabla 2 — Operadores:
    1. Lanzar dados
    2. Entrar ficha al tablero
    3. Mover ficha
    4. Completar ficha
    5. Capturar ficha rival
    6. Obtener turno extra
    7. Cambiar turno
    8. Perder turno
"""

import random


# ── Tabla 1 — Dominios ───────────────────────────────────────────────

J_1, J_2 = 1, 2

espera, activa, completada = "espera", "activa", "completada"

vacío = 0
sí, no = True, False

ROSETAS = {4, 8, 14, 18, 20}


# ── Tabla 1 — Entidades ──────────────────────────────────────────────

class Ficha:
    """F_i  →  n_i, J_i, S_i, P_i"""
    __slots__ = ("n", "J", "S", "P")

    def __init__(self, n, J):
        self.n = n
        self.J = J
        self.S = espera
        self.P = 0


class Casilla:
    """C_n  →  O_n, U_n, ρ_n"""
    __slots__ = ("O", "U", "ρ")

    def __init__(self, n):
        self.O = vacío
        self.U = n
        self.ρ = sí if n in ROSETAS else no


class Ur:
    """Estado del juego:  Ur = (J)·(F)·(D)·(T)·(C)"""
    __slots__ = ("R", "M", "F", "D", "τ", "C")

    def __init__(self):
        self.R = {J_1: 4, J_2: 4}
        self.M = {J_1: 0, J_2: 0}
        self.F = {i: Ficha(n=((i - 1) % 4) + 1,
                           J=J_1 if i <= 4 else J_2)
                  for i in range(1, 9)}
        self.D = {k: 0 for k in range(1, 5)}
        self.τ = J_1
        self.C = {n: Casilla(n) for n in range(1, 21)}

    @property
    def ΣD(self):
        return sum(self.D.values())


# ── Tabla 2 — Operadores ─────────────────────────────────────────────

def lanzar_dados(ur):
    """
    1. Lanzar dados.
       Si  τ = J_j   →   D_k = {0,1} para k = 1..4,   ΣD = D_1+D_2+D_3+D_4.
    """
    for k in range(1, 5):
        ur.D[k] = random.randint(0, 1)


def entrar_ficha_al_tablero(ur, F_i, destino):
    """
    2. Entrar ficha al tablero.
       Si  R_j > 0  ∧  ΣD > 0  ∧  O_destino ≠ J_j
       →   S_i = activa,  P_i = ΣD,  O_destino = J_j,  R_j = R_j − 1.
    """
    F_i.S = activa
    F_i.P = ur.ΣD
    ur.C[destino].O = F_i.J
    ur.R[F_i.J] -= 1


def mover_ficha(ur, F_i, origen, destino):
    """
    3. Mover ficha.
       Si  S_i = activa  ∧  ΣD > 0  ∧  P_i + ΣD ≤ 14  ∧  O_destino ≠ J_j
           ∧  ¬(O_destino = J_rival  ∧  ρ_destino = sí)
       →   O_origen = vacío,  P_i = P_i + ΣD,  O_destino = J_j.
    """
    ur.C[origen].O = vacío
    F_i.P += ur.ΣD
    ur.C[destino].O = F_i.J


def completar_ficha(ur, F_i, origen):
    """
    4. Completar ficha.
       Si  S_i = activa  ∧  P_i + ΣD = 15
       →   S_i = completada,  P_i = 0,  M_j = M_j + 1,  O_origen = vacío.
    """
    ur.C[origen].O = vacío
    F_i.S = completada
    F_i.P = 0
    ur.M[F_i.J] += 1


def capturar_ficha_rival(ur, F_rival):
    """
    5. Capturar ficha rival.
       Si  O_destino = J_rival  ∧  U_destino ∈ {5..12}  ∧  ρ_destino = no
       →   S_rival = espera,  P_rival = 0,  R_rival = R_rival + 1.
    """
    F_rival.S = espera
    F_rival.P = 0
    ur.R[F_rival.J] += 1


def obtener_turno_extra(ur):
    """
    6. Obtener turno extra.
       Si  ρ_destino = sí   →   τ = J_j   (se mantiene).
    """
    pass


def cambiar_turno(ur):
    """
    7. Cambiar turno.
       Si  ρ_destino = no   →   τ = J_opuesto.
    """
    ur.τ = J_2 if ur.τ == J_1 else J_1


def perder_turno(ur):
    """
    8. Perder turno.
       Si  ΣD = 0   →   τ = J_opuesto.
    """
    ur.τ = J_2 if ur.τ == J_1 else J_1
