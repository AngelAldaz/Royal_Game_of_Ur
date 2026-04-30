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

> Nota importante: las **variables del código tienen exactamente los mismos
> nombres que el análisis EEO 3.1**. La IA accede a `state.R`, `state.M`,
> `state.tau`, `state.sigma_D`, `state.O`, `state.D`, `state.F` y a las
> propiedades de cada `Piece` (`piece.n`, `piece.J`, `piece.S`, `piece.P`).
> No hay traducción intermedia: el código *es* el modelo formal.

---

## 2. Mapeo IA ↔ Tabla 1 (variables)

La función de evaluación lee directamente las variables EEO:

| Variable EEO | Código | Uso en la IA |
| ------------ | ------ | ------------ |
| `R_j` | `state.R[j]` | Reserva del jugador (peso negativo si es propia) |
| `M_j` | `state.M[j]` | Fichas en meta — peso muy alto |
| `tau` | `state.tau` | Quién decide en cada nodo del árbol |
| `sigma_D` | `state.sigma_D` | Suma de dados; rama del nodo CHANCE |
| `D_k` | `state.D[k-1]` | Resultado individual de cada dado |
| `O_n` | `state.O[n]` | Detección de capturas, bloqueos y rosetas ocupadas |
| `n_i`, `J_i` | `piece.n`, `piece.J` | Identificación de cada ficha al recorrer el árbol |
| `S_i` | `piece.S` | `espera`, `activa`, `completada` — filtra movimientos legales |
| `P_i` | `piece.P` | Posición en el camino — base del progreso heurístico |

---

## 3. Mapeo IA ↔ Tabla 2 (operadores y reglas)

La IA no implementa operadores nuevos: usa **literalmente las mismas funciones**
del módulo `game/operators.py` que el jugador humano. Cada operador de la
Tabla 2 corresponde a una rama de la búsqueda y a un componente de la heurística.

### Operador 1 — Lanzar dados

```
Condición:  tau = J_j  AND  ¬dice_rolled
Efecto:     D_k ∈ {0,1} aleatorio,  sigma_D = Σ D_k
```

**En la IA:** los nodos CHANCE del árbol modelan este operador como una
distribución de probabilidad sobre las 5 sumas posibles `sigma_D ∈ {0..4}`.
El valor de un nodo CHANCE es:

$$
V_{\text{chance}}(s) = \sum_{\sigma_D = 0}^{4} P(\sigma_D) \cdot V_{\text{decision}}(s, \sigma_D)
$$

con `P(sigma_D)` siguiendo la distribución binomial $B(4, 0.5)$:

| sigma_D | 0 | 1 | 2 | 3 | 4 |
| ------- | - | - | - | - | - |
| P | 1/16 | 4/16 | 6/16 | 4/16 | 1/16 |

Definida en `ai.py` como `DICE_PROB`.

### Operador 2 — Entrar ficha al tablero

```
Condición:  R_j > 0 ∧ sigma_D > 0 ∧ O_destino ≠ J_j
Efecto:     S_i: espera→activa,  P_i = sigma_D,  O_destino = J_j,  R_j -= 1
```

**En la IA:** `legal_moves(state)` filtra movimientos según esta condición.
Cuando la IA evalúa "entrar ficha", la heurística suma:

- `−12 · R_j` antes (alta penalización por reserva grande propia)
- `+8 · sigma_D` después (progreso lineal por la nueva posición)

### Operador 3 — Mover ficha

```
Condición:  S_i = activa ∧ P_i + sigma_D ≤ 14 ∧ casillas válidas
Efecto:     O_origen = vacío,  P_i += sigma_D,  O_destino = J_j
```

**En la IA:** se exploran TODAS las fichas activas como posibles movimientos.
La heurística valora el avance no linealmente:

```python
progress = 8·P_i + (P_i − 8)²    si P_i ≥ 8    # acelera cerca de la meta
         = 8·P_i                 si P_i < 8
```

Esto refleja que avanzar de 13→14 vale más que avanzar de 1→2.

### Operador 4 — Capturar ficha rival

```
Condición:  O_destino = J_rival ∧ U_destino ∈ {5..12} ∧ rho_destino = NO
Efecto:     S_rival: activa→espera,  P_rival = 0,  R_rival += 1
```

**En la IA:** la captura es un evento muy valorado. En el ordenamiento de
movimientos:

```python
if state.O[target] == oponente:
    quick_score += 300   # explora capturas primero -> mejor poda
```

Y en la heurística, capturar produce:
- `+12` por el `R_rival` que aumenta
- En el siguiente turno, la ficha capturada estará en espera, por lo que el
  rival pierde el progreso `P_i`-related que tenía.

Además, `_threat_score()` mide cuántas sumas `sigma_D` permitirían al rival
capturarte a ti (probabilidad ponderada hasta 60 puntos), evitando jugadas
suicidas.

### Operador 5 — Completar ficha

```
Condición:  S_i = activa ∧ P_i + sigma_D = 15 (suma exacta)
Efecto:     S_i: activa→completada,  P_i = 0,  M_j += 1,  O_origen = vacío
```

**En la IA:** completar ficha es la jugada de mayor peso heurístico:

```python
score += 1200 · M_j     # cada ficha en meta vale 1200
```

En el ordenamiento heurístico, `quick_score = +1000` para completar — siempre
se explora primero.

### Operador 6 — Obtener turno extra (roseta)

```
Condición:  rho_destino = SI
Efecto:     tau se mantiene
```

**En la IA:** muy valorado porque permite encadenar jugadas. La heurística
asigna:

- `+50` si la ficha cae en la roseta segura `C8` (turno extra + inmunidad)
- `+35` para cualquier otra roseta (4, 14, 18, 20)

En el ordenamiento de movimientos:

```python
if C.is_rosette(target):
    quick_score += 200
```

Importante: el árbol de búsqueda respeta el turno extra. Después de aplicar
`apply_move`, si `tau` no cambió, el siguiente nodo de decisión vuelve a ser
de la IA (MAX), no del rival.

### Operador 7 — Cambiar turno

```
Condición:  movimiento completado AND rho_destino = NO
Efecto:     tau = J_opuesto
```

**En la IA:** define la alternancia MAX/MIN del árbol. Cada llamada a
`apply_move` ya cambia `tau` automáticamente cuando corresponde, así que el
algoritmo solo necesita revisar `state.tau` para saber si el siguiente nodo
es MAX o MIN.

```python
if state.tau == maximizing_player:
    # nodo MAX
else:
    # nodo MIN
```

### Operador 8 — Perder turno (sigma_D = 0)

```
Condición:  sigma_D = 0  OR  no hay movimientos legales
Efecto:     tau = J_opuesto
```

**En la IA:** se modela en los nodos CHANCE para `sigma_D = 0`:

```python
if s == 0:
    ops.lose_turn(child)
    expected += prob · expectiminimax(child, depth-1, ...)
```

La probabilidad de este caso es 1/16 (6.25 %) y se incluye en la esperanza.

---

## 4. Estructura del árbol Expectiminimax

```
Estado raíz (mi turno, debo lanzar dados)
    ▼
Nodo CHANCE (Operador 1: Lanzar dados)
    ├── sigma_D = 0  [P=1/16]  → Operador 8 (perder turno) → siguiente nivel
    ├── sigma_D = 1  [P=4/16]
    ├── sigma_D = 2  [P=6/16]
    ├── sigma_D = 3  [P=4/16]
    └── sigma_D = 4  [P=1/16]
              │
              ▼
        Nodo MAX (mi decisión)
        Movimientos legales en este sigma_D:
            ├── Mover F_1  (Op 3)
            ├── Mover F_2  (Op 3 + posible Op 4 captura)
            ├── Entrar F_3 (Op 2)
            └── Completar F_4 (Op 5)
                    │
                    ▼
              Si rho_destino = NO:
                Nodo CHANCE del rival (su lanzamiento)
              Si rho_destino = SI (Op 6 turno extra):
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
    para cada suma sigma_D ∈ {1..4}:
        si alguna ficha rival puede llegar exactamente a mi casilla con sigma_D:
            threats_prob += P(sigma_D)
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

| Componente del análisis 3.1 | Código |
| --------------------------- | ------ |
| Tabla 1 (entidades, atributos) | [`game/state.py`](../game/state.py) — clases `Piece` y `GameState` con atributos `R, M, F, D, tau, O` y `n, J, S, P` |
| Tabla 2 — Op. 1 Lanzar dados | `roll_dice(state)` en [`operators.py`](../game/operators.py) |
| Tabla 2 — Op. 2 Entrar ficha | rama `S == ESPERA` de `apply_move` |
| Tabla 2 — Op. 3 Mover ficha | rama `S == ACTIVA` de `apply_move` |
| Tabla 2 — Op. 4 Capturar | bloque "rival_occupant != 0..." dentro de `apply_move` |
| Tabla 2 — Op. 5 Completar | rama `new_P == META_POS` de `apply_move` |
| Tabla 2 — Op. 6 Turno extra | bloque `if C.is_rosette(landed_square): info["extra_turn"] = True` |
| Tabla 2 — Op. 7 Cambiar turno | `change_turn(state)` |
| Tabla 2 — Op. 8 Perder turno | `lose_turn(state)` |
| Espacio de estados S | Dominio de la búsqueda (cada nodo es un `GameState`) |
| Vector de 102 componentes | Visible en el panel EEO de la UI en tiempo real |

---

## 8. Posibles preguntas en defensa

**P: ¿Por qué Expectiminimax y no Minimax?**
R: Porque el juego tiene un componente aleatorio (los 4 dados), entonces no
basta con MAX/MIN: hace falta un tipo adicional de nodo (CHANCE) que calcule
la esperanza ponderada por probabilidad. Es la generalización estándar de
Minimax para juegos con azar (Russell & Norvig, *AI: A Modern Approach*).

**P: ¿Cómo conecta el código con el análisis EEO?**
R: Las clases del modelo (`GameState`, `Piece`) usan EXACTAMENTE las mismas
variables del análisis (Tabla 1). Cada operador de la Tabla 2 está
implementado como una función o rama del archivo `operators.py`. La IA
opera sobre ese mismo modelo: `legal_moves()` aplica las condiciones de
aplicabilidad, `apply_move()` aplica los efectos. No hay traducción.

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
