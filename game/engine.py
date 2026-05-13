"""
Motor del juego: orquesta los operadores literales de `eeo.py` (Tabla 2)
con los helpers de `rules.py`, y añade el control de sesión que NO es
parte del modelo EEO formal (banderas de turno, descripción del último
evento, jugador ganador).
"""

from . import eeo
from . import rules


class Game(eeo.Ur):
    """Ur + control de sesión (dice_rolled, last_event, winner)."""

    __slots__ = ("dice_rolled", "last_event", "winner")

    def __init__(self):
        super().__init__()
        self.dice_rolled = False
        self.last_event = "Inicio del juego"
        self.winner = None

    def is_terminal(self):
        return self.winner is not None

    def pieces_of(self, J):
        return [f for f in self.F.values() if f.J == J]

    def get_piece(self, J, n):
        for f in self.F.values():
            if f.J == J and f.n == n:
                return f
        return None

    def occupant_at(self, U):
        if U is None or U not in self.C:
            return eeo.vacío
        return self.C[U].O

    def piece_at_square(self, U):
        if U is None:
            return None
        for f in self.F.values():
            if f.S == eeo.activa and rules.square_at(f.J, f.P) == U:
                return f
        return None

    def clone(self):
        new = Game.__new__(Game)
        new.R = dict(self.R)
        new.M = dict(self.M)
        new.F = {i: eeo.Ficha.__new__(eeo.Ficha) for i in self.F}
        for i, f in self.F.items():
            new.F[i].n, new.F[i].J = f.n, f.J
            new.F[i].S, new.F[i].P = f.S, f.P
        new.D = dict(self.D)
        new.τ = self.τ
        new.C = {n: eeo.Casilla.__new__(eeo.Casilla) for n in self.C}
        for n, c in self.C.items():
            new.C[n].O, new.C[n].U, new.C[n].ρ = c.O, c.U, c.ρ
        new.dice_rolled = self.dice_rolled
        new.last_event = self.last_event
        new.winner = self.winner
        return new


def lanzar_dados(game):
    """Operador 1 + bookkeeping (marca dados lanzados)."""
    eeo.lanzar_dados(game)
    game.dice_rolled = True
    game.last_event = f"Jugador {game.τ} lanza dados: ΣD = {game.ΣD}"


def perder_turno(game):
    """Operador 8 + bookkeeping (limpia dados)."""
    game.last_event = f"Jugador {game.τ} pierde turno (ΣD = {game.ΣD})"
    eeo.perder_turno(game)
    for k in game.D:
        game.D[k] = 0
    game.dice_rolled = False


def legal_moves(game):
    """Fichas movibles para τ con ΣD actual."""
    if game.ΣD == 0 or game.is_terminal():
        return []

    moves = []
    s = game.ΣD
    for F_i in game.pieces_of(game.τ):
        if F_i.S == eeo.completada:
            continue

        new_P = s if F_i.S == eeo.espera else F_i.P + s

        if new_P > rules.META_POS:
            continue
        if new_P == rules.META_POS:
            moves.append(F_i)
            continue

        destino = rules.square_at(F_i.J, new_P)
        ocupante = game.occupant_at(destino)
        if ocupante == F_i.J:
            continue
        if destino == rules.ROSETA_SEGURA and ocupante != eeo.vacío and ocupante != F_i.J:
            continue
        moves.append(F_i)

    return moves


def apply_move(game, F_i):
    """
    Aplica la jugada componiendo los operadores 2-7 según el caso:

        S_i = espera                  →  (Op.5 Capturar + ) Op.2 Entrar
        S_i = activa, P_i + ΣD < 15   →  (Op.5 Capturar + ) Op.3 Mover
        S_i = activa, P_i + ΣD = 15   →  Op.4 Completar
        Luego  Op.6 (ρ_destino = sí)  o  Op.7 (ρ_destino = no).
    """
    assert F_i.J == game.τ
    assert game.ΣD > 0

    s = game.ΣD
    info = {"captured": None, "completed": False, "extra_turn": False,
            "entered": False, "event": ""}

    if F_i.S == eeo.espera:
        destino = rules.square_at(F_i.J, s)

        F_rival = game.piece_at_square(destino)
        if F_rival is not None and F_rival.J != F_i.J:
            eeo.capturar_ficha_rival(game, F_rival)
            info["captured"] = F_rival

        eeo.entrar_ficha_al_tablero(game, F_i, destino)
        info["entered"] = True
        info["event"] = f"J{F_i.J} entra ficha {F_i.n} en casilla {destino}"

    else:  # F_i.S == activa
        new_P = F_i.P + s
        origen = rules.square_at(F_i.J, F_i.P)

        if new_P == rules.META_POS:
            eeo.completar_ficha(game, F_i, origen)
            info["completed"] = True
            info["event"] = f"J{F_i.J} completa ficha {F_i.n} (a meta)"
            if game.M[F_i.J] == 4:
                game.winner = F_i.J
        else:
            destino = rules.square_at(F_i.J, new_P)

            F_rival = game.piece_at_square(destino)
            if F_rival is not None and F_rival.J != F_i.J:
                eeo.capturar_ficha_rival(game, F_rival)
                info["captured"] = F_rival

            eeo.mover_ficha(game, F_i, origen, destino)
            info["event"] = f"J{F_i.J} mueve ficha {F_i.n} a casilla {destino}"

    landed = rules.square_of(F_i)
    if not info["completed"] and landed is not None and rules.is_rosette(landed):
        info["extra_turn"] = True
        eeo.obtener_turno_extra(game)
    elif not game.is_terminal():
        eeo.cambiar_turno(game)

    descr = info["event"]
    if info["captured"] is not None:
        cap = info["captured"]
        descr += f" | captura ficha {cap.n} de J{cap.J}"
    if info["extra_turn"]:
        descr += " | turno extra (roseta)"
    game.last_event = descr

    for k in game.D:
        game.D[k] = 0
    game.dice_rolled = False

    return info
