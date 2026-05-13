# Inteligencia Artificial del oponente

Documento de referencia para explicar la IA del juego en defensa oral.

---

## 1. Resumen ejecutivo

La IA del oponente usa **Expectiminimax** con **profundidad 3**, **poda
alfa-beta** parcial y una **función de evaluación heurística**. Es una
aplicación directa de búsqueda en espacio de estados sobre exactamente el
espacio formalizado en el análisis EEO 3.1.

- Algoritmo: Expectiminimax (variante de Minimax para juegos con azar).
- Profundidad: 3 niveles.
- Tiempo por decisión: ~200 ms en mid-game.
- Implementación: [`game/ai.py`](../game/ai.py).
- Resultados: ~95 % de victorias contra un agente aleatorio.

> Nota importante: las **variables del código son 1:1 con el análisis EEO
> 3.1**, incluyendo Unicode (`τ`, `ΣD`, `ρ`). [`game/eeo.py`](../game/eeo.py)
> contiene **solo** lo que aparece en las Tablas 1 y 2 (sin paths, sin
> helpers, sin orquestador); lo derivado vive en [`rules.py`](../game/rules.py)
> y [`engine.py`](../game/engine.py). La IA accede a `state.R[j]`,
> `state.M[j]`, `state.τ`, `state.ΣD`, `state.D[k]` (k ∈ {1..4}),
> `state.F[i]` (i ∈ {1..8}), `state.C[n].O / .U / .ρ`, más las propiedades
> de cada `Piece` (`piece.n`, `piece.J`, `piece.S`, `piece.P`). No hay
> traducción intermedia: el código *es* el modelo formal.

---

## 2. Mapeo IA ↔ Tabla 1 (variables)

La función de evaluación lee directamente las variables EEO:

| Variable EEO | Código (1:1) | Uso en la IA |
| ------------ | ------------ | ------------ |
| `R_j` | `state.R[j]` | Reserva del jugador (peso negativo si es propia) |
| `M_j` | `state.M[j]` | Fichas en meta — peso muy alto |
| `τ`   | `state.τ`    | Quién decide en cada nodo del árbol |
| `ΣD`  | `state.ΣD`   | Suma de dados; rama del nodo CHANCE |
| `D_k` | `state.D[k]` | Resultado individual de cada dado (k ∈ {1..4}) |
| `O_n` | `state.C[n].O` | Detección de capturas, bloqueos y rosetas ocupadas |
| `U_n` | `state.C[n].U` | Ubicación física (estática, `U_n = n`) |
| `ρ_n` | `state.C[n].ρ` | Roseta (estática, `True` para `n ∈ {4, 8, 14, 18, 20}`) |
| `n_i` | `state.F[i].n` | Número de ficha (i ∈ {1..8}) |
| `J_i` | `state.F[i].J` | Jugador dueño |
| `S_i` | `state.F[i].S` | `espera`, `activa`, `completada` — filtra movimientos legales |
| `P_i` | `state.F[i].P` | Posición en el camino — base del progreso heurístico |

---

## 3. Mapeo IA ↔ Tabla 2 (operadores y reglas)

La IA no implementa operadores nuevos: usa **literalmente las mismas funciones**
del módulo [`game/eeo.py`](../game/eeo.py) que el jugador humano. Los 8
operadores de la Tabla 2 están expuestos como funciones en el **orden y con
los nombres exactos** del análisis:

  1. `lanzar_dados`
  2. `entrar_ficha_al_tablero`
  3. `mover_ficha`
  4. `completar_ficha`
  5. `capturar_ficha_rival`
  6. `obtener_turno_extra`
  7. `cambiar_turno`
  8. `perder_turno`

`engine.apply_move` es el orquestador que los compone según el caso.

### Operador 1 — Lanzar dados

```
Condición:  τ = J_j  AND  ¬dice_rolled
Efecto:     D_k ∈ {0,1} aleatorio,  ΣD = Σ D_k
```

**En la IA:** los nodos CHANCE del árbol modelan este operador como una
distribución de probabilidad sobre las 5 sumas posibles `ΣD ∈ {0..4}`.
El valor de un nodo CHANCE es:

$$
V_{\text{chance}}(s) = \sum_{\ΣD = 0}^{4} P(\ΣD) \cdot V_{\text{decision}}(s, \ΣD)
$$

con `P(ΣD)` siguiendo la distribución binomial $B(4, 0.5)$:

| ΣD | 0 | 1 | 2 | 3 | 4 |
| ------- | - | - | - | - | - |
| P | 1/16 | 4/16 | 6/16 | 4/16 | 1/16 |

Definida en `ai.py` como `DICE_PROB`.

### Operador 2 — Entrar ficha al tablero

```
Condición:  R_j > 0 ∧ ΣD > 0 ∧ O_destino ≠ J_j
Efecto:     S_i: espera→activa,  P_i = ΣD,  O_destino = J_j,  R_j -= 1
```

**En la IA:** `legal_moves(state)` filtra movimientos según esta condición.
Cuando la IA evalúa "entrar ficha", la heurística suma:

- `−12 · R_j` antes (alta penalización por reserva grande propia)
- `+8 · ΣD` después (progreso lineal por la nueva posición)

### Operador 3 — Mover ficha

```
Condición:  S_i = activa ∧ P_i + ΣD ≤ 14 ∧ casillas válidas
Efecto:     O_origen = vacío,  P_i += ΣD,  O_destino = J_j
```

**En la IA:** se exploran TODAS las fichas activas como posibles movimientos.
La heurística valora el avance no linealmente:

```python
progress = 8·P_i + (P_i − 8)²    si P_i ≥ 8    # acelera cerca de la meta
         = 8·P_i                 si P_i < 8
```

Esto refleja que avanzar de 13→14 vale más que avanzar de 1→2.

### Operador 4 — Completar ficha

```
Condición:  S_i = activa ∧ P_i + ΣD = 15 (suma exacta)
Efecto:     S_i: activa→completada,  P_i = 0,  M_j += 1,  O_origen = vacío
```

**En la IA:** completar ficha es la jugada de mayor peso heurístico:

```python
score += 1200 · M_j     # cada ficha en meta vale 1200
```

En el ordenamiento heurístico, `quick_score = +1000` para completar — siempre
se explora primero.

### Operador 5 — Capturar ficha rival

```
Condición:  O_destino = J_rival ∧ U_destino ∈ {5..12} ∧ ρ_destino = NO
Efecto:     S_rival: activa→espera,  P_rival = 0,  R_rival += 1
```

**En la IA:** la captura es un evento muy valorado. En el ordenamiento de
movimientos:

```python
if state.occupant_at(target) == rules.opponent(piece.J):
    quick_score += 300   # explora capturas primero -> mejor poda
```

Y en la heurística, capturar produce:
- `+12` por el `R_rival` que aumenta
- En el siguiente turno, la ficha capturada estará en espera, por lo que el
  rival pierde el progreso `P_i`-related que tenía.

Además, `_threat_score()` mide cuántas sumas `ΣD` permitirían al rival
capturarte a ti (probabilidad ponderada hasta 60 puntos), evitando jugadas
suicidas.

### Operador 6 — Obtener turno extra (roseta)

```
Condición:  ρ_destino = SI
Efecto:     τ se mantiene
```

**En la IA:** muy valorado porque permite encadenar jugadas. La heurística
asigna:

- `+50` si la ficha cae en la roseta segura `C8` (turno extra + inmunidad)
- `+35` para cualquier otra roseta (4, 14, 18, 20)

En el ordenamiento de movimientos:

```python
if rules.is_rosette(target):
    quick_score += 200
```

Importante: el árbol de búsqueda respeta el turno extra. Después de aplicar
`apply_move`, si `τ` no cambió, el siguiente nodo de decisión vuelve a ser
de la IA (MAX), no del rival.

### Operador 7 — Cambiar turno

```
Condición:  movimiento completado AND ρ_destino = NO
Efecto:     τ = J_opuesto
```

**En la IA:** define la alternancia MAX/MIN del árbol. Cada llamada a
`apply_move` ya cambia `τ` automáticamente cuando corresponde, así que el
algoritmo solo necesita revisar `state.τ` para saber si el siguiente nodo
es MAX o MIN.

```python
if state.τ == maximizing_player:
    # nodo MAX
else:
    # nodo MIN
```

### Operador 8 — Perder turno

```
Condición:  ΣD = 0  OR  no hay movimientos legales
Efecto:     τ = J_opuesto
```

**En la IA:** se modela en los nodos CHANCE para `ΣD = 0`:

```python
if s == 0:
    engine.perder_turno(child)
    expected += prob · expectiminimax(child, depth-1, ...)
```

La probabilidad de este caso es 1/16 (6.25 %) y se incluye en la esperanza.

---

## 4. Estructura del árbol Expectiminimax

```
Estado raíz (mi turno, debo lanzar dados)
    ▼
Nodo CHANCE (Operador 1: Lanzar dados)
    ├── ΣD = 0  [P=1/16]  → Operador 8 (perder turno) → siguiente nivel
    ├── ΣD = 1  [P=4/16]
    ├── ΣD = 2  [P=6/16]
    ├── ΣD = 3  [P=4/16]
    └── ΣD = 4  [P=1/16]
              │
              ▼
        Nodo MAX (mi decisión)
        Movimientos legales en este ΣD:
            ├── Mover F_1  (Op 3)
            ├── Mover F_2  (Op 3 + posible Op 5 captura)
            ├── Entrar F_3 (Op 2)
            └── Completar F_4 (Op 4)
                    │
                    ▼
              Si ρ_destino = NO:
                Nodo CHANCE del rival (su lanzamiento)
              Si ρ_destino = SI (Op 6 turno extra):
                Otro nodo CHANCE mío (sigo yo)
```

La poda alfa-beta solo se aplica entre nodos MAX y MIN. Los nodos CHANCE no
se podan porque su valor es una esperanza que requiere TODAS las ramas.

---

## 5. Función de evaluación (componentes y pesos)

Resumen de `evaluate(state, player)`:

| Concepto | Peso | Justificación |
| -------- | ---- | ------------- |
| `+1200 · M[player]` | +1200/ficha | Es el objetivo del juego — peso máximo |
| `−1200 · M[enemy]` | −1200/ficha | Simétrico |
| `+12 · R[enemy]` | +12 | Le falta progresar |
| `−12 · R[player]` | −12 | Simétrico |
| Avance lineal: `+8 · P_i` | variable | Fichas más adelante valen más |
| Avance no lineal: `+(P_i − 8)²` | si `P_i ≥ 8` | Acelera cerca de meta |
| Privada de salida `P_i ≥ 13` | +60 | Casillas seguras y a 1-2 pasos de meta |
| Roseta segura C8 | +50 | Roseta + inmunidad a captura |
| Otras rosetas | +35 | Solo turno extra |
| `_threat_score` | hasta ±60 | Análisis probabilístico de amenazas reales |
| Estado terminal (gano) | +100 000 | Corta búsqueda con valor enorme |
| Estado terminal (pierdo) | −100 000 | Simétrico |

### Análisis dinámico de amenazas

El análisis estático de "estar en zona compartida" es ingenuo. El método
`_threat_score()` calcula la **probabilidad real** de captura:

```python
para cada ficha propia activa en zona compartida (no segura):
    threats_prob = 0
    para cada suma ΣD ∈ {1..4}:
        si alguna ficha rival puede llegar exactamente a mi casilla con ΣD:
            threats_prob += P(ΣD)
    score -= int(60 · threats_prob)   # exposición = malo para mí
```

Esto lo convierte en una heurística **probabilísticamente informada**.

---

## 6. Resultados experimentales

| Configuración | Tiempo / jugada | Resultado |
| ------------- | --------------- | --------- |
| Depth 2 | ~16 ms | 100 % vs random (20/20) |
| **Depth 3** (default) | **~200 ms** | **95 % vs random (19/20)** |
| Depth 4 | ~2.5 s | (impráctico para juego interactivo) |

---

## 7. Trazabilidad código ↔ análisis EEO

[`game/eeo.py`](../game/eeo.py) contiene **exclusivamente** lo que está en las
Tablas 1 y 2 del análisis, sin ruido. Todo lo demás (paths, zonas, helpers,
orquestador, control de turno) vive en archivos separados:

  - [`game/eeo.py`](../game/eeo.py)    — Tabla 1 (entidades + dominios) y Tabla 2 (8 operadores).
  - [`game/rules.py`](../game/rules.py) — reglas derivadas: `PATH_J_1`, `PATH_J_2`, `META_POS`, `CASILLAS_*`, `ROSETA_SEGURA`, helpers (`square_at`, `square_of`, `is_rosette`, `is_shared`, `opponent`).
  - [`game/engine.py`](../game/engine.py) — `Game` (extiende `GameState` con `dice_rolled`, `last_event`, `winner`), `apply_move` (orquestador) y `legal_moves` (consulta).

### Tabla 1 — entidades y dominios (en `eeo.py`)

| Tabla 1 | Código |
| ------- | ------ |
| Clases: `Casilla` (`O`, `U`, `ρ`), `Piece` (`n`, `J`, `S`, `P`), `GameState` (`R`, `M`, `F`, `D`, `τ`, `ΣD`, `C[n]`) | atributos exactos según las columnas "Variable" de la Tabla 1 |
| Dominios: `J_1`, `J_2`, `ESPERA`, `ACTIVA`, `COMPLETADA`, `ROSETAS` | constantes |
| Cardinalidades: `FICHAS_POR_JUGADOR = 4`, `NUM_DADOS = 4`, `NUM_CASILLAS = 20` | constantes |

### Tabla 2 — operadores (en `eeo.py`, en el orden exacto del análisis)

| Nº | Operador               | Función en `eeo.py`                              |
| -- | ---------------------- | ------------------------------------------------ |
| 1  | Lanzar dados           | `lanzar_dados(state)`                            |
| 2  | Entrar ficha al tablero | `entrar_ficha_al_tablero(state, piece, target)` |
| 3  | Mover ficha            | `mover_ficha(state, piece, origin, target)`     |
| 4  | Completar ficha        | `completar_ficha(state, piece, origin)`         |
| 5  | Capturar ficha rival   | `capturar_ficha_rival(state, rival)`            |
| 6  | Obtener turno extra    | `obtener_turno_extra(state)`                    |
| 7  | Cambiar turno          | `cambiar_turno(state)`                          |
| 8  | Perder turno           | `perder_turno(state)`                           |

### Lo que NO está en las tablas (vive fuera de `eeo.py`)

| Concepto                          | Código |
| --------------------------------- | ------ |
| Camino `P_i → U_n` por jugador    | `rules.PATH_J_1`, `rules.PATH_J_2`, `rules.path_for`, `rules.square_at`, `rules.square_of` |
| Posición transitoria a meta       | `rules.META_POS = 15` |
| Zonas del tablero                 | `rules.CASILLAS_COMPARTIDAS`, `rules.CASILLAS_PRIVADAS_J_1`, `rules.CASILLAS_PRIVADAS_J_2` |
| Roseta 8 inmune a captura         | `rules.ROSETA_SEGURA` |
| Helpers                           | `rules.is_rosette`, `rules.is_shared`, `rules.opponent` |
| Estado de sesión (control turno)  | `engine.Game` (campos `dice_rolled`, `last_event`, `winner`; métodos `is_terminal`, `pieces_of`, `get_piece`, `occupant_at`, `piece_at_square`, `clone`) |
| Wrapper de bookkeeping            | `engine.lanzar_dados` (Op. 1 + marca dados), `engine.perder_turno` (Op. 8 + limpia dados) |
| Orquestador de un movimiento      | `engine.apply_move(state, piece)` compone Op. 2/3, 5, 4, 6 y 7 |
| Consulta de movimientos legales   | `engine.legal_moves(state)` |
| Espacio de estados S              | Dominio de la búsqueda (cada nodo es un `engine.Game`) |
| Vector de 102 componentes         | Visible en el panel EEO de la UI en tiempo real |

---

## 8. Posibles preguntas en defensa

**P: ¿Por qué Expectiminimax y no Minimax?**
R: Porque el juego tiene un componente aleatorio (los 4 dados), entonces no
basta con MAX/MIN: hace falta un tipo adicional de nodo (CHANCE) que calcule
la esperanza ponderada por probabilidad. Es la generalización estándar de
Minimax para juegos con azar (Russell & Norvig, *AI: A Modern Approach*).

**P: ¿Cómo conecta el código con el análisis EEO?**
R: Toda la Tabla 1 y la Tabla 2 viven en un único archivo:
[`game/eeo.py`](../game/eeo.py). Las clases del modelo (`Casilla`, `Piece`,
`GameState`) usan EXACTAMENTE las mismas variables del análisis (Tabla 1).
Cada operador de la Tabla 2 es una función con su nombre en español
(`lanzar_dados`, `entrar_ficha`, `mover_ficha`, `capturar_ficha`,
`completar_ficha`, `obtener_turno_extra`, `cambiar_turno`, `perder_turno`),
con la fila correspondiente de la Tabla 2 como docstring. La IA opera sobre
ese mismo modelo: `legal_moves()` aplica las condiciones de aplicabilidad y
`apply_move()` orquesta los efectos. No hay traducción.

**P: ¿La IA es determinista?**
R: La heurística sí: dado el mismo estado y los mismos dados, siempre elige
el mismo movimiento. La aleatoriedad solo viene del lanzamiento de los dados,
modelado como nodo CHANCE.

**P: ¿Por qué profundidad 3?**
R: Empíricamente. Profundidad 4 tarda 2.5s/jugada (impráctico para juego
interactivo); profundidad 2 ya gana 100% a random pero se beneficia de un
nivel extra para anticipar respuestas del rival ponderadas por azar. La
heurística aporta más que profundidad adicional: con `_threat_score` ya
embebemos información de "1 ply adelante" en la propia evaluación.

**P: ¿Por qué 1200 puntos por ficha en meta?**
R: Pesos calibrados experimentalmente. La idea es que ningún otro factor
debe poder "compensar" sacrificar una ficha en meta. Como el progreso lineal
máximo es ~190 (8·14 + 36 + 60 + 50 ≈ 190), un peso de 1200 garantiza que
completar siempre dominará la decisión.

**P: ¿Puede empatar?**
R: No. El juego termina cuando alguien lleva sus 4 fichas a meta — siempre
hay un ganador.

**P: ¿La heurística garantiza la jugada óptima?**
R: No. Garantizar óptimo requeriría explorar el árbol completo, lo cual es
inviable. La heurística aproxima el valor de los estados no terminales con
la información disponible. Sin embargo, en estados cercanos a la victoria
(profundidad de búsqueda alcanza estados terminales), la decisión sí es
óptima dentro del horizonte explorado.

**P: ¿Qué pasa si dos movimientos tienen la misma evaluación?**
R: Gana el que aparece primero en el orden recorrido. Como pre-ordeno
heurísticamente (capturas → rosetas → completar → mayor progreso), el
desempate favorece la jugada más "agresiva".

**P: ¿Cuál es la complejidad?**
R: En el peor caso, $O((b \cdot c)^d)$ con $b$ ≈ 4–8 (movimientos legales),
$c = 5$ (sumas posibles de dados), $d$ = profundidad efectiva. Con poda
alfa-beta y ordenamiento heurístico, en la práctica se reduce
significativamente.

**P: ¿Qué se podría mejorar?**
R: Tablas de transposición (memoization), poda alfa-beta sobre nodos chance
con cotas probabilísticas, profundidad iterativa con time limit, o sustituir
la heurística por una red neuronal entrenada por self-play. Para el alcance
del proyecto no es necesario.
