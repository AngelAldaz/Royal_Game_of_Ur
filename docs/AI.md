# Inteligencia Artificial del oponente

Documento de referencia para explicar la IA del juego en defensa oral.

---

## 1. Resumen ejecutivo

La IA del oponente es una **heurística greedy con pesos**: para cada
jugada legal calcula un puntaje sumando pesos según qué consigue
(completar, capturar, caer en roseta, etc.) y elige la jugada con
mayor puntaje. No hay árbol de búsqueda, no hay recursión, no hay
cálculo de probabilidades.

- Algoritmo: greedy 1-ply (sólo evalúa la jugada inmediata).
- Tiempo por decisión: ~0 ms.
- Implementación: [`game/ai.py`](../game/ai.py) (~50 líneas).
- Resultados: **~92 %** de victorias contra un agente aleatorio.

> La IA opera sobre el mismo modelo EEO que el jugador humano. Lee
> directamente las variables de la Tabla 1 (`state.J[j].R`,
> `state.T.ΣD`, `state.F[i].P`, `state.C[n].O`, …) y llama a los
> operadores de la Tabla 2 a través de [`engine`](../game/engine.py)
> (`engine.legal_moves`, `engine.apply_move`). No hay traducción
> intermedia: el código *es* el modelo formal.

---

## 2. Cómo elige una jugada

```python
def choose_move(state):
    moves = engine.legal_moves(state)
    if not moves:
        return None
    return max(moves, key=lambda F_i: puntaje(state, F_i))
```

Eso es todo el "algoritmo": pide los movimientos legales (Tabla 2,
condiciones de aplicabilidad) y devuelve el que maximiza `puntaje`.

---

## 3. Función `puntaje` — los 5 pesos

```python
PESO_COMPLETAR = 1000   # llegar a meta
PESO_CAPTURAR  = 500    # capturar ficha rival
PESO_ROSETA    = 300    # caer en roseta (turno extra)
PESO_ENTRAR    = 50     # sacar ficha de la reserva
PESO_AVANCE    = 10     # × nueva posición en el camino
```

| Peso              | Valor | Justificación                                                  |
| ----------------- | ----- | -------------------------------------------------------------- |
| `PESO_COMPLETAR`  | 1000  | Llevar una ficha a meta es el objetivo del juego — domina todo |
| `PESO_CAPTURAR`   | 500   | Envía una ficha rival a reserva (le quita progreso al rival)   |
| `PESO_ROSETA`     | 300   | Da turno extra (encadena jugadas)                              |
| `PESO_ENTRAR`     | 50    | Sacar una ficha de reserva es preferible a quedarse atrás      |
| `PESO_AVANCE`     | 10    | Multiplicado por `P_i` nuevo: avanzar más vale más             |

La función literal:

```python
def puntaje(state, F_i):
    s = state.T.ΣD
    new_P = s if F_i.S == eeo.espera else F_i.P + s

    if new_P == rules.META_POS:
        return PESO_COMPLETAR

    destino = rules.square_at(F_i.J, new_P)
    total = PESO_AVANCE * new_P

    if state.occupant_at(destino) == rules.opponent(F_i.J):
        total += PESO_CAPTURAR
    if rules.is_rosette(destino):
        total += PESO_ROSETA
    if F_i.S == eeo.espera:
        total += PESO_ENTRAR

    return total
```

Ejemplo: con `ΣD = 4`, mover una ficha a la casilla 8 (roseta segura)
desde la casilla 4 (otra roseta) capturando ficha rival da:

    PESO_CAPTURAR + PESO_ROSETA + PESO_AVANCE · 8
    =      500    +      300    +      80     =  880

---

## 4. Mapeo IA ↔ Tabla 1 (variables que lee)

| Variable EEO | Acceso en código        | Uso en la IA                              |
| ------------ | ----------------------- | ----------------------------------------- |
| `τ`          | `state.T.τ`             | Identifica al jugador en turno            |
| `ΣD`         | `state.T.ΣD`            | Cuánto avanza la ficha en esta jugada     |
| `S_i`        | `F_i.S`                 | Distingue espera/activa para calcular `new_P` |
| `P_i`        | `F_i.P`                 | Posición actual de la ficha               |
| `J_i`        | `F_i.J`                 | Saber si una ficha es propia o rival      |
| `O_n`        | `state.C[n].O`          | Detectar ficha rival en la casilla destino |
| `ρ_n`        | `rules.is_rosette(n)`   | Detectar si el destino es roseta          |

La IA **no lee** `R_j`, `M_j`, `n_i`, `U_n` ni los `D_k` individuales:
con los 7 atributos anteriores le basta para decidir.

---

## 5. Mapeo IA ↔ Tabla 2 (operadores)

La IA delega TODO al motor (`engine.py`), que a su vez compone los
operadores literales de la Tabla 2:

| Operador (Tabla 2)        | Cuándo lo dispara la IA                       |
| ------------------------- | --------------------------------------------- |
| 1. Lanzar dados           | Antes de pedir `choose_move` (en el bucle de `main.py`) |
| 2. Entrar ficha al tablero | Si elige una ficha con `S_i = espera`         |
| 3. Mover ficha            | Si elige una ficha con `S_i = activa` y `P_i + ΣD < 15` |
| 4. Completar ficha        | Si elige una ficha con `P_i + ΣD = 15`        |
| 5. Capturar ficha rival   | Implícito: si el destino tiene ficha rival, se dispara antes de Op.2 ó Op.3 |
| 6. Obtener turno extra    | Implícito: si cae en roseta, el motor lo aplica |
| 7. Cambiar turno          | Implícito: si no cayó en roseta, el motor lo aplica |
| 8. Perder turno           | Si `legal_moves` devuelve `[]` o `ΣD = 0`, `main.py` invoca `engine.perder_turno` |

`engine.apply_move(state, F_i)` ejecuta los operadores 2-7 según el caso.

---

## 6. Resultados experimentales

| Configuración          | Tiempo / jugada | Resultado            |
| ---------------------- | --------------- | -------------------- |
| Heurística greedy      | ~0 ms           | **92 %** vs random (46/50 cada lado) |

---

## 7. Posibles preguntas en defensa

**P: ¿Por qué greedy en vez de Minimax/Expectiminimax?**
R: Por simplicidad y transparencia. La función `puntaje` se puede leer y
entender en 10 segundos: cinco pesos, una jugada. Un algoritmo de búsqueda
profunda añadiría complejidad sin que la mejora sea decisiva para mostrar
el ciclo EEO funcionando: lo importante del proyecto es la correspondencia
1:1 con las Tablas 1 y 2 del análisis, no la sofisticación del jugador
automático.

**P: ¿La IA es determinista?**
R: Sí. Dado el mismo estado y los mismos dados, siempre elige la misma
ficha. La única aleatoriedad del juego viene de `lanzar_dados`.

**P: ¿Qué pasa si dos jugadas tienen el mismo puntaje?**
R: Python `max(..., key=...)` devuelve la primera con el máximo, así que
gana la primera en el orden de `legal_moves` (que recorre las fichas
`F_1..F_8` en orden de índice).

**P: ¿Por qué `PESO_AVANCE = 10` y no algo mayor?**
R: Para que el avance acumulado nunca compense una captura o una roseta
del rival. El máximo `PESO_AVANCE · P_i` posible es `10 × 14 = 140`, que
sigue siendo menor que `PESO_ROSETA = 300` y `PESO_CAPTURAR = 500`. Así
las jugadas "interesantes" (capturas, rosetas, completar) dominan
siempre.

**P: ¿Puede empatar?**
R: No. El juego termina cuando alguien lleva sus 4 fichas a meta —
siempre hay un ganador.

**P: ¿Cómo conecta el código con el análisis EEO?**
R: Toda la Tabla 1 y la Tabla 2 viven en
[`game/eeo.py`](../game/eeo.py). Las 5 clases del modelo (`Jugador`,
`Ficha`, `Dado`, `Tablero`, `Casilla`) corresponden a las 5 entidades de
la Tabla 1; los 8 operadores de la Tabla 2 son funciones con su nombre
exacto. La IA llama a `engine.legal_moves` (que aplica las condiciones
de aplicabilidad) y a `engine.apply_move` (que aplica los efectos). No
hay traducción intermedia.

**P: ¿Qué se podría mejorar?**
R: Añadir un peso negativo por "exposición a captura" (cuántas sumas de
dados del rival permitirían capturarme), o mirar 1 ply adelante para
detectar trampas. También se podría volver a un algoritmo de búsqueda
(Expectiminimax) como en versiones anteriores, pero el costo en
complejidad de código no se justifica para este proyecto.
