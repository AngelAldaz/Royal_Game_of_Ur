"""
Operadores y reglas del juego, mapeados 1 a 1 a la Tabla 2 del analisis EEO 3.1.

Operadores:
  1. Lanzar dados
  2. Entrar ficha al tablero
  3. Mover ficha
  4. Capturar ficha rival   (efecto colateral de mover)
  5. Completar ficha (a meta)
  6. Obtener turno extra    (efecto de roseta)
  7. Cambiar turno
  8. Perder turno (dados = 0)

Cada funcion modifica el GameState in-place y devuelve un dict con info del cambio,
o se aplica como parte de un operador compuesto (apply_move).
"""

import random
from . import constants as C


# --------- 1. Lanzar dados ---------

def roll_dice(state, rng=None):
    """
    Operador: Lanzar dados.
    Condicion: es turno del jugador y aun no ha lanzado dados en este turno.
    Efecto: D_k = aleatorio{0,1} para k=1..4, dice_rolled=True.
    """
    rng = rng or random
    state.dice = [rng.randint(0, 1) for _ in range(C.NUM_DADOS)]
    state.dice_rolled = True
    state.last_event = f"Jugador {state.turn} lanza dados: suma = {state.dice_sum}"
    return {"dice": list(state.dice), "sum": state.dice_sum}


# --------- 7/8. Cambiar turno / perder turno ---------

def change_turn(state):
    """Pasa el turno al oponente y limpia los dados."""
    state.turn = C.opponent(state.turn)
    state.dice = [0, 0, 0, 0]
    state.dice_rolled = False


def lose_turn(state):
    """
    Operador: Perder turno.
    Condicion: dice_sum == 0 (o no hay movimientos legales).
    Efecto: el turno pasa al oponente.
    """
    state.last_event = f"Jugador {state.turn} pierde turno (suma dados = {state.dice_sum})"
    change_turn(state)


# --------- Movimientos legales ---------

def legal_moves(state):
    """
    Devuelve lista de fichas movibles para el jugador en turno con la suma de dados actual.
    Cada elemento es la propia ficha (Piece). Si esta vacia, el jugador no puede mover.

    Una ficha es movible si:
      - state == espera y la casilla destino (posicion = sumaD) esta libre o no es ficha propia
      - state == activa y posicion + sumaD <= 15 y casilla destino libre o no es propia
        ademas: si la casilla destino es la roseta segura (8) y esta ocupada por rival -> no movible
    """
    if state.dice_sum == 0 or state.is_terminal():
        return []

    moves = []
    s = state.dice_sum
    for piece in state.pieces_of(state.turn):
        if piece.state == C.COMPLETADA:
            continue

        if piece.state == C.ESPERA:
            new_pos = s
            if new_pos > 14:
                continue
            target_square = C.square_at(piece.owner, new_pos)
            occupant = state.occupant_at(target_square)
            if occupant == piece.owner:
                continue
            # casilla 8 segura: no se puede capturar
            if target_square == C.ROSETA_SEGURA and occupant != 0 and occupant != piece.owner:
                continue
            moves.append(piece)

        elif piece.state == C.ACTIVA:
            new_pos = piece.position + s
            if new_pos > C.META_POS:
                continue  # se pasa de la meta, no permitido
            if new_pos == C.META_POS:
                # salida exacta -> siempre legal (la casilla origen se libera)
                moves.append(piece)
                continue
            target_square = C.square_at(piece.owner, new_pos)
            occupant = state.occupant_at(target_square)
            if occupant == piece.owner:
                continue
            if target_square == C.ROSETA_SEGURA and occupant != 0 and occupant != piece.owner:
                continue
            moves.append(piece)

    return moves


# --------- 2/3/4/5/6. Aplicar movimiento ---------

def apply_move(state, piece):
    """
    Aplica el movimiento de la ficha indicada usando la suma de dados actual.
    Compone los operadores: Entrar / Mover / Capturar / Completar / Turno extra.

    Retorna un dict con eventos ocurridos: captured (Piece o None), completed (bool),
    extra_turn (bool), entered (bool), event (str descripcion).
    """
    assert piece.owner == state.turn, "La ficha no pertenece al jugador en turno"
    assert state.dice_sum > 0, "No se puede mover con suma de dados 0"

    s = state.dice_sum
    info = {"captured": None, "completed": False, "extra_turn": False, "entered": False, "event": ""}

    # Casilla origen
    origin_square = piece.square()  # None si está en espera

    # Caso A: Entrar ficha al tablero
    if piece.state == C.ESPERA:
        new_pos = s
        target_square = C.square_at(piece.owner, new_pos)

        # capturar si hay rival
        rival_occupant = state.occupant_at(target_square)
        if rival_occupant != 0 and rival_occupant != piece.owner:
            captured = _piece_at_square(state, target_square)
            _send_to_reserve(state, captured)
            info["captured"] = captured

        # actualizar ficha
        piece.state = C.ACTIVA
        piece.position = new_pos
        state.players_reserva[piece.owner] -= 1
        state.ocupantes[target_square] = piece.owner
        info["entered"] = True
        info["event"] = f"J{piece.owner} entra ficha {piece.number} en casilla {target_square}"

    # Caso B: Mover ficha activa
    else:
        new_pos = piece.position + s

        # Liberar casilla origen
        if origin_square is not None:
            state.ocupantes[origin_square] = 0

        if new_pos == C.META_POS:
            # Completar
            piece.state = C.COMPLETADA
            piece.position = 0
            state.players_meta[piece.owner] += 1
            info["completed"] = True
            info["event"] = f"J{piece.owner} completa ficha {piece.number} (a meta)"
        else:
            target_square = C.square_at(piece.owner, new_pos)

            # capturar si hay rival
            rival_occupant = state.occupant_at(target_square)
            if rival_occupant != 0 and rival_occupant != piece.owner:
                captured = _piece_at_square(state, target_square)
                _send_to_reserve(state, captured)
                info["captured"] = captured

            piece.position = new_pos
            state.ocupantes[target_square] = piece.owner
            info["event"] = f"J{piece.owner} mueve ficha {piece.number} a casilla {target_square}"

    # Comprobar victoria
    if state.players_meta[piece.owner] == C.FICHAS_POR_JUGADOR:
        state.winner = piece.owner

    # Roseta -> turno extra
    if not info["completed"]:
        landed_square = piece.square()
        if landed_square is not None and C.is_rosette(landed_square):
            info["extra_turn"] = True

    # Construir descripcion completa del evento (para el panel)
    descr = info["event"]
    if info["captured"]:
        cap = info["captured"]
        descr += f" | captura ficha {cap.number} de J{cap.owner}"
    if info["extra_turn"]:
        descr += " | turno extra (roseta)"
    state.last_event = descr

    # Turno: si no hubo turno extra, cambiar
    state.dice = [0, 0, 0, 0]
    state.dice_rolled = False
    if not info["extra_turn"] and not state.is_terminal():
        state.turn = C.opponent(state.turn)

    return info


# --------- helpers internos ---------

def _piece_at_square(state, square):
    """Encuentra la ficha activa que está en la casilla dada."""
    for p in state.pieces:
        if p.state == C.ACTIVA and p.square() == square:
            return p
    return None


def _send_to_reserve(state, piece):
    """Envia una ficha capturada de vuelta a la reserva."""
    piece.state = C.ESPERA
    piece.position = 0
    state.players_reserva[piece.owner] += 1
