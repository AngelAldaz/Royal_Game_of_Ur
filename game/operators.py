"""
Operadores y reglas del juego, mapeados 1 a 1 a la Tabla 2 del análisis EEO 3.1.

Los nombres de las variables (R, M, n, J, S, P, D, tau, sigma_D, O) son
exactamente los del análisis EEO documentado en la Tabla 1.

Operadores implementados:
  1. Lanzar dados            -> roll_dice(state)
  2. Entrar ficha al tablero -> apply_move(state, piece)   [rama ESPERA]
  3. Mover ficha             -> apply_move(state, piece)   [rama ACTIVA]
  4. Capturar ficha rival    -> efecto compuesto dentro de apply_move
  5. Completar ficha (meta)  -> efecto compuesto dentro de apply_move
  6. Obtener turno extra     -> efecto compuesto dentro de apply_move
  7. Cambiar turno           -> change_turn(state)
  8. Perder turno            -> lose_turn(state)
"""

import random
from . import constants as C


# --------- 1. Lanzar dados ---------

def roll_dice(state, rng=None):
    """
    Operador: Lanzar dados.

    Condición de aplicabilidad:
        tau = J_j  (es turno del jugador j)  AND  no se han lanzado los dados aún

    Efecto:
        D_k = aleatorio{0, 1}  para k = 1..4
        sigma_D = sum(D_k)
    """
    rng = rng or random
    state.D = [rng.randint(0, 1) for _ in range(C.NUM_DADOS)]
    state.dice_rolled = True
    state.last_event = f"Jugador {state.tau} lanza dados: ΣD = {state.sigma_D}"
    return {"D": list(state.D), "sigma_D": state.sigma_D}


# --------- 7/8. Cambiar turno / perder turno ---------

def change_turn(state):
    """Operador: Cambiar turno. Pasa el turno al oponente y limpia los dados."""
    state.tau = C.opponent(state.tau)
    state.D = [0, 0, 0, 0]
    state.dice_rolled = False


def lose_turn(state):
    """
    Operador: Perder turno.

    Condición:  sigma_D == 0   ó   no hay movimientos legales

    Efecto: tau = J_opuesto
    """
    state.last_event = f"Jugador {state.tau} pierde turno (ΣD = {state.sigma_D})"
    change_turn(state)


# --------- Movimientos legales ---------

def legal_moves(state):
    """
    Devuelve la lista de fichas movibles para el jugador en turno (tau)
    con la suma de dados actual (sigma_D).

    Una ficha F_i es movible si:
      - S_i == espera y la casilla destino (P_i = sigma_D) está libre o no es propia
      - S_i == activa y P_i + sigma_D <= 15 y casilla destino libre o no propia
      - además: si destino es la roseta segura (8) y está ocupada por rival,
        no se puede entrar (regla de roseta segura).
    """
    if state.sigma_D == 0 or state.is_terminal():
        return []

    moves = []
    s = state.sigma_D
    for piece in state.pieces_of(state.tau):
        if piece.S == C.COMPLETADA:
            continue

        if piece.S == C.ESPERA:
            new_P = s
            if new_P > 14:
                continue
            target_square = C.square_at(piece.J, new_P)
            occupant = state.occupant_at(target_square)
            if occupant == piece.J:
                continue
            if target_square == C.ROSETA_SEGURA and occupant != 0 and occupant != piece.J:
                continue
            moves.append(piece)

        elif piece.S == C.ACTIVA:
            new_P = piece.P + s
            if new_P > C.META_POS:
                continue  # se pasa de la meta
            if new_P == C.META_POS:
                # Salida exacta -> Operador "Completar ficha", siempre legal
                moves.append(piece)
                continue
            target_square = C.square_at(piece.J, new_P)
            occupant = state.occupant_at(target_square)
            if occupant == piece.J:
                continue
            if target_square == C.ROSETA_SEGURA and occupant != 0 and occupant != piece.J:
                continue
            moves.append(piece)

    return moves


# --------- 2/3/4/5/6. Aplicar movimiento (operador compuesto) ---------

def apply_move(state, piece):
    """
    Aplica el movimiento de la ficha indicada usando la suma de dados actual.
    Compone los operadores: Entrar / Mover / Capturar / Completar / Turno extra.

    Retorna un dict con eventos ocurridos: captured (Piece o None), completed (bool),
    extra_turn (bool), entered (bool), event (str descripción).
    """
    assert piece.J == state.tau, "La ficha no pertenece al jugador en turno"
    assert state.sigma_D > 0, "No se puede mover con sigma_D = 0"

    s = state.sigma_D
    info = {"captured": None, "completed": False, "extra_turn": False,
            "entered": False, "event": ""}

    origin_square = piece.square()  # None si está en espera

    # ===== Operador 2: Entrar ficha al tablero =====
    if piece.S == C.ESPERA:
        new_P = s
        target_square = C.square_at(piece.J, new_P)

        # ===== Operador 4: Capturar ficha rival (si la casilla destino tiene rival) =====
        rival_occupant = state.occupant_at(target_square)
        if rival_occupant != 0 and rival_occupant != piece.J:
            captured = _piece_at_square(state, target_square)
            _send_to_reserve(state, captured)
            info["captured"] = captured

        # Aplicar entrada
        piece.S = C.ACTIVA
        piece.P = new_P
        state.R[piece.J] -= 1
        state.O[target_square] = piece.J
        info["entered"] = True
        info["event"] = f"J{piece.J} entra ficha {piece.n} en casilla {target_square}"

    # ===== Operador 3: Mover ficha activa =====
    else:
        new_P = piece.P + s

        # Liberar casilla origen
        if origin_square is not None:
            state.O[origin_square] = 0

        if new_P == C.META_POS:
            # ===== Operador 5: Completar ficha =====
            piece.S = C.COMPLETADA
            piece.P = 0
            state.M[piece.J] += 1
            info["completed"] = True
            info["event"] = f"J{piece.J} completa ficha {piece.n} (a meta)"
        else:
            target_square = C.square_at(piece.J, new_P)

            # ===== Operador 4: Capturar ficha rival =====
            rival_occupant = state.occupant_at(target_square)
            if rival_occupant != 0 and rival_occupant != piece.J:
                captured = _piece_at_square(state, target_square)
                _send_to_reserve(state, captured)
                info["captured"] = captured

            piece.P = new_P
            state.O[target_square] = piece.J
            info["event"] = f"J{piece.J} mueve ficha {piece.n} a casilla {target_square}"

    # Comprobar victoria
    if state.M[piece.J] == C.FICHAS_POR_JUGADOR:
        state.winner = piece.J

    # ===== Operador 6: Obtener turno extra (si la ficha cayó en roseta) =====
    if not info["completed"]:
        landed_square = piece.square()
        if landed_square is not None and C.is_rosette(landed_square):
            info["extra_turn"] = True

    # Construir descripción completa del evento
    descr = info["event"]
    if info["captured"]:
        cap = info["captured"]
        descr += f" | captura ficha {cap.n} de J{cap.J}"
    if info["extra_turn"]:
        descr += " | turno extra (roseta)"
    state.last_event = descr

    # ===== Operador 7: Cambiar turno (si NO hubo turno extra) =====
    state.D = [0, 0, 0, 0]
    state.dice_rolled = False
    if not info["extra_turn"] and not state.is_terminal():
        state.tau = C.opponent(state.tau)

    return info


# --------- helpers internos ---------

def _piece_at_square(state, square):
    """Encuentra la ficha activa que está en la casilla dada."""
    for p in state.F:
        if p.S == C.ACTIVA and p.square() == square:
            return p
    return None


def _send_to_reserve(state, piece):
    """Efecto del operador Capturar: envía una ficha de vuelta a su reserva."""
    piece.S = C.ESPERA
    piece.P = 0
    state.R[piece.J] += 1
