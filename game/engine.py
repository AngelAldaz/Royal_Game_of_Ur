"""
Motor del juego: orquesta los operadores literales de `eeo.py` (Tabla 2)
usando los helpers de `rules.py`, y añade el control de sesión que no
forma parte del modelo EEO formal (banderas de turno, descripción del
último evento, jugador ganador).

  - `Game`         : extiende `eeo.GameState` con los campos auxiliares
                     `dice_rolled`, `last_event`, `winner` y métodos de
                     consulta (`pieces_of`, `get_piece`, `occupant_at`,
                     `piece_at_square`, `is_terminal`, `clone`).
  - `lanzar_dados` : wrapper del operador 1 + bookkeeping.
  - `perder_turno` : wrapper del operador 8 + bookkeeping.
  - `apply_move`   : compone los operadores 2 a 7 de la Tabla 2 según
                     el caso (entrada / movimiento / completar, con o
                     sin captura, con o sin roseta).
  - `legal_moves`  : consulta de fichas movibles para τ con ΣD actual.
"""

from . import eeo
from . import rules


# ══════════════════════════════════════════════════════════════════════
# Estado de sesión (extiende el vector EEO con campos auxiliares)
# ══════════════════════════════════════════════════════════════════════

class Game(eeo.GameState):
    """
    Hereda los atributos de Tabla 1 (R, M, F, D, τ, ΣD, C) y añade
    tres campos auxiliares que NO están en la Tabla 1:

        dice_rolled : True si los dados ya se lanzaron este turno.
        last_event  : descripción textual del último operador aplicado.
        winner      : jugador ganador (None si la partida sigue).
    """

    __slots__ = ("dice_rolled", "last_event", "winner")

    def __init__(self):
        super().__init__()
        self.dice_rolled = False
        self.last_event = "Inicio del juego"
        self.winner = None

    # ----- consultas convenientes -----

    def is_terminal(self):
        return self.winner is not None

    def pieces_of(self, J):
        return [p for p in self.F.values() if p.J == J]

    def get_piece(self, J, n):
        for p in self.F.values():
            if p.J == J and p.n == n:
                return p
        return None

    def occupant_at(self, square):
        """O_n para la casilla física `square` (0 si no es válida)."""
        if square is None or square not in self.C:
            return 0
        return self.C[square].O

    def piece_at_square(self, square):
        """Ficha activa que ocupa `square`, o None."""
        if square is None:
            return None
        for p in self.F.values():
            if p.S == eeo.ACTIVA and rules.square_at(p.J, p.P) == square:
                return p
        return None

    # ----- utilidades -----

    def clone(self):
        new = Game.__new__(Game)
        new.R = dict(self.R)
        new.M = dict(self.M)
        new.F = {i: p.clone() for i, p in self.F.items()}
        new.D = dict(self.D)
        new.τ = self.τ
        new.C = {n: c.clone() for n, c in self.C.items()}
        new.dice_rolled = self.dice_rolled
        new.last_event = self.last_event
        new.winner = self.winner
        return new


# ══════════════════════════════════════════════════════════════════════
# Wrappers de operadores que requieren bookkeeping de sesión
# ══════════════════════════════════════════════════════════════════════

def lanzar_dados(game, rng=None):
    """Aplica el Operador 1 (Tabla 2) y marca los dados como lanzados."""
    eeo.lanzar_dados(game, rng)
    game.dice_rolled = True
    game.last_event = f"Jugador {game.τ} lanza dados: ΣD = {game.ΣD}"


def perder_turno(game):
    """Aplica el Operador 8 (Tabla 2) y limpia los dados para el rival."""
    game.last_event = f"Jugador {game.τ} pierde turno (ΣD = {game.ΣD})"
    eeo.perder_turno(game)
    for k in game.D:
        game.D[k] = 0
    game.dice_rolled = False


# ══════════════════════════════════════════════════════════════════════
# Consulta: movimientos legales
# ══════════════════════════════════════════════════════════════════════

def legal_moves(game):
    """Fichas movibles para τ con ΣD actual (no es operador de Tabla 2)."""
    if game.ΣD == 0 or game.is_terminal():
        return []

    moves = []
    s = game.ΣD
    for piece in game.pieces_of(game.τ):
        if piece.S == eeo.COMPLETADA:
            continue

        if piece.S == eeo.ESPERA:
            new_P = s
        else:  # ACTIVA
            new_P = piece.P + s

        if new_P > rules.META_POS:
            continue
        if new_P == rules.META_POS:
            # Operador 4 (Completar) siempre es legal con suma exacta
            moves.append(piece)
            continue

        target = rules.square_at(piece.J, new_P)
        occupant = game.occupant_at(target)
        if occupant == piece.J:
            continue
        if target == rules.ROSETA_SEGURA and occupant != 0 and occupant != piece.J:
            continue
        moves.append(piece)

    return moves


# ══════════════════════════════════════════════════════════════════════
# Orquestador: aplica un movimiento completo del jugador
# ══════════════════════════════════════════════════════════════════════

def apply_move(game, piece):
    """
    Aplica el movimiento elegido componiendo los operadores de la
    Tabla 2 en el siguiente orden:

        Si S_i = espera:
            (Op. 5 Capturar  +)  Op. 2 Entrar ficha al tablero
        Si S_i = activa  y  P_i + ΣD < 15:
            (Op. 5 Capturar  +)  Op. 3 Mover ficha
        Si S_i = activa  y  P_i + ΣD = 15:
            Op. 4 Completar ficha
        Luego:
            Op. 6 Obtener turno extra  (si ρ_destino = sí)
              ó    Op. 7 Cambiar turno (en caso contrario)
    """
    assert piece.J == game.τ, "La ficha no pertenece al jugador en turno"
    assert game.ΣD > 0, "No se puede mover con ΣD = 0"

    s = game.ΣD
    info = {"captured": None, "completed": False, "extra_turn": False,
            "entered": False, "event": ""}

    # ---- Operador principal: Entrar (2) / Mover (3) / Completar (4) ----
    if piece.S == eeo.ESPERA:
        target = rules.square_at(piece.J, s)

        # Op. 5 (Capturar ficha rival) si en el destino hay ficha rival
        rival = game.piece_at_square(target)
        if rival is not None and rival.J != piece.J:
            eeo.capturar_ficha_rival(game, rival)
            info["captured"] = rival

        # Op. 2 (Entrar ficha al tablero)
        eeo.entrar_ficha_al_tablero(game, piece, target)
        info["entered"] = True
        info["event"] = f"J{piece.J} entra ficha {piece.n} en casilla {target}"

    else:  # piece.S == ACTIVA
        new_P = piece.P + s
        origin = rules.square_at(piece.J, piece.P)

        if new_P == rules.META_POS:
            # Op. 4 (Completar ficha)
            eeo.completar_ficha(game, piece, origin)
            info["completed"] = True
            info["event"] = f"J{piece.J} completa ficha {piece.n} (a meta)"
            if game.M[piece.J] == eeo.FICHAS_POR_JUGADOR:
                game.winner = piece.J
        else:
            target = rules.square_at(piece.J, new_P)

            # Op. 5 (Capturar ficha rival)
            rival = game.piece_at_square(target)
            if rival is not None and rival.J != piece.J:
                eeo.capturar_ficha_rival(game, rival)
                info["captured"] = rival

            # Op. 3 (Mover ficha)
            eeo.mover_ficha(game, piece, origin, target)
            info["event"] = f"J{piece.J} mueve ficha {piece.n} a casilla {target}"

    # ---- Op. 6 Turno extra (roseta)  vs  Op. 7 Cambiar turno ----
    landed = rules.square_of(piece)
    if not info["completed"] and landed is not None and rules.is_rosette(landed):
        info["extra_turn"] = True
        eeo.obtener_turno_extra(game)
    elif not game.is_terminal():
        eeo.cambiar_turno(game)

    # ---- Bookkeeping (no es operador de Tabla 2) ----
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
