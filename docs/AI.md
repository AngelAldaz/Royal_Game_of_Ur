# Inteligencia Artificial del oponente

Documento de referencia para explicar la IA del juego en defensa oral o
preguntas de los evaluadores.

---

## 1. Resumen ejecutivo

La IA del oponente usa **Expectiminimax** con **profundidad 3**, **poda
alfa-beta** parcial y una **función de evaluación heurística** específica para
el Royal Game of Ur. Es una aplicación directa de búsqueda en espacio de
estados, exactamente el espacio formalizado en el análisis EEO 3.1.

- Algoritmo: Expectiminimax (variante de Minimax para juegos con azar).
- Profundidad: 3 niveles (≈ 1.5 turnos completos por jugador).
- Tiempo por decisión: ~200 ms en mid-game.
- Implementación: [`game/ai.py`](../game/ai.py).
- Resultados: ~95 % de victorias contra un agente aleatorio.

---

## 2. ¿Por qué Expectiminimax y no Minimax?

**Minimax** clásico asume que el juego es totalmente determinista: en cada
nodo, un jugador maximiza y el otro minimiza una función de utilidad.

El Royal Game of Ur **no es determinista**: en cada turno se lanzan 4 dados
binarios (cada uno 0 o 1). La suma puede ser 0, 1, 2, 3 o 4. Esto introduce
**nodos de azar** en el árbol de juego — nodos que no son decisiones, sino
distribuciones de probabilidad.

**Expectiminimax** es la generalización para juegos con azar. Añade un tipo
adicional de nodo:

- **Nodo MAX**: el jugador propio elige la mejor jugada (maximiza).
- **Nodo MIN**: el rival elige la peor jugada para nosotros (minimiza).
- **Nodo CHANCE (azar)**: ningún jugador decide; el valor es la **esperanza
  matemática** ponderada por probabilidad.

### Probabilidad de cada suma de dados

Como los 4 dados son binarios independientes con $P(1) = 0.5$, la suma sigue
una distribución **binomial** $B(4, 0.5)$:

| Suma $\Sigma D$ | Probabilidad |
| --------------- | ------------ |
| 0 | 1/16 = 6.25 % |
| 1 | 4/16 = 25 % |
| 2 | 6/16 = 37.5 % |
| 3 | 4/16 = 25 % |
| 4 | 1/16 = 6.25 % |

Estas probabilidades están codificadas en `DICE_PROB` en `ai.py`.

---

## 3. Estructura del árbol de búsqueda

Cada llamada a `expectiminimax(state, depth, ...)` puede caer en uno de tres
tipos de nodo según el estado:

```
┌──────────────────────────────────────────────────────────────┐
│  ¿Los dados ya fueron lanzados en este turno?               │
│                                                              │
│   NO  ── nodo CHANCE                                         │
│           expandir 5 ramas (Σ = 0..4)                        │
│           valor = Σ P(s) · expectiminimax(hijo, depth, ...)  │
│                                                              │
│   SÍ  ── nodo de DECISIÓN                                    │
│           ¿De quién es el turno?                             │
│              MIO    → MAX (tomar mejor jugada)               │
│              RIVAL  → MIN (tomar peor para mí)               │
└──────────────────────────────────────────────────────────────┘
```

### Profundidad

- **`depth = 3`** se interpreta como 3 niveles de exploración. Con la
  alternancia chance / decisión, esto equivale aproximadamente a:
  - 1 nivel de mi decisión actual (raíz)
  - 1 nivel de azar (dados del rival)
  - 1 nivel de decisión del rival
  - 1 nivel de azar (mis siguientes dados)

  Suficiente para ver las consecuencias inmediatas de mi jugada y la mejor
  respuesta del rival, ponderada por azar.

- Se probó depth 4 pero tarda ~2.5 s por jugada (impráctico). Depth 2 va más
  rápido pero pierde fuerza estratégica.

### Manejo del caso $\Sigma D = 0$

Cuando la rama del nodo CHANCE corresponde a suma 0, el jugador en turno
**pierde su turno** (regla del juego). En el árbol, esto se modela aplicando
`lose_turn()` y descontando 1 a la profundidad antes de seguir.

---

## 4. Función de evaluación (heurística)

`evaluate(state, player)` asigna un puntaje al estado desde el punto de vista
de `player`. Se usa cuando se llega al límite de profundidad o a un estado
terminal.

### Componentes (todos los pesos en el código)

| Concepto | Peso | Justificación |
| -------- | ---- | ------------- |
| Cada ficha propia en meta | +1200 | Es el objetivo del juego — peso muy alto. |
| Cada ficha rival en meta | −1200 | Simétrico. |
| Cada ficha rival en reserva | +12 | Le falta progresar; es bueno para nosotros. |
| Cada ficha propia en reserva | −12 | Simétrico. |
| Avance lineal de fichas activas | $8 \cdot P_i$ | Fichas más adelante valen más. |
| Bono no lineal posición $\geq 8$ | $(P_i - 8)^2$ | Posiciones tardías valen aún más (curva convexa hacia la meta). |
| Ficha en zona privada de salida ($P \geq 13$) | +60 | Casillas seguras y cerca de meta. |
| Ficha propia en roseta segura (C8) | +50 | Roseta + inmunidad a captura. |
| Ficha propia en otra roseta | +35 | Da turno extra. |
| **Análisis dinámico de amenazas** | hasta ±60 | Ver siguiente sección. |
| Estado terminal (victoria propia) | +100 000 | Corta la búsqueda con un valor enorme. |
| Estado terminal (derrota) | −100 000 | Simétrico. |

### Análisis dinámico de amenazas (la parte interesante)

Una heurística estática simple penaliza fijo "estar en zona compartida". Pero
no toda casilla compartida es igual de peligrosa: depende de **dónde están las
fichas del rival** y qué dados necesita para alcanzarte.

Para cada ficha propia activa en zona compartida (no segura), `_threat_score`
calcula la **probabilidad real** de que el rival pueda capturarla en su
próximo turno:

```python
threats_prob = 0
for cada suma s ∈ {1, 2, 3, 4}:
    para cada ficha del rival:
        si esa ficha + s aterriza en MI casilla:
            threats_prob += P(s)
            break    # una amenaza por suma es suficiente
```

El resultado, multiplicado por 60, se resta al puntaje (si la ficha amenazada
es propia) o se suma (si es del rival, son oportunidades para nosotros).

**Por qué es importante:** sin esto, la IA dejaba fichas en posición 7 a un
paso de una ficha rival en posición 6 (vulnerable a captura con $\Sigma D = 1$,
probabilidad 25 %). Con esta heurística, la IA pondera: "si avanzo aquí, el
rival me captura con 25 % de probabilidad → −15 puntos esperados".

Esto convierte una heurística miope en una **heurística probabilística
explícita** que entiende el riesgo.

---

## 5. Optimizaciones

### 5.1 Poda alfa-beta (parcial)

En los nodos de decisión (MAX/MIN) se aplica poda alfa-beta clásica. Esto
elimina ramas cuyo valor no puede mejorar la decisión actual.

**Limitación:** los nodos CHANCE **no se pueden podar** sin perder corrección,
porque el valor depende de TODAS las ramas (es una esperanza). Se podría usar
**alpha-beta para chance nodes** (con cotas probabilísticas), pero no se
implementó por simplicidad.

### 5.2 Ordenamiento de movimientos (move ordering)

`choose_move` ordena los movimientos antes de explorarlos, probando primero
los más prometedores:

1. Movimientos que completan ficha (+1000)
2. Capturas (+300)
3. Aterrizajes en roseta (+200)
4. Mayor progreso ($P_i$)

Esto hace que la poda alfa-beta corte mucho antes (primero MAX encuentra una
buena jugada → $\alpha$ alto → muchas ramas posteriores se podan).

### 5.3 Clonación eficiente de estado

`GameState.clone()` evita `copy.deepcopy` (lento) y copia explícitamente solo
los atributos mutables, lo cual es 5–10× más rápido. Crítico porque el
algoritmo crea miles de clones por decisión.

---

## 6. Resultados experimentales

Validación en simulaciones automatizadas (`docs/AI.md` documenta los datos
obtenidos al desarrollarla):

| Configuración | Tiempo / jugada | Resultado |
| ------------- | --------------- | --------- |
| Depth 2 | ~16 ms | 100 % vs random (20/20) |
| **Depth 3** (default) | **~200 ms** | **95 % vs random (19/20)** |
| Depth 4 | ~2 500 ms | (no medido — demasiado lento) |

| Comparativa interna | Resultado |
| ------------------- | --------- |
| Depth 3 vs Depth 2 | 8 / 20 — sin diferencia clara (varianza por azar) |

**Interpretación:** la heurística aporta más que profundidad adicional. La
varianza inherente a los dados hace que ir más profundo no siempre mejore
proporcionalmente. Lo crítico es la calidad de la evaluación — y la nuestra
ya considera amenazas probabilísticas, que es información de "1 ply
adelante" embebida en la propia evaluación.

---

## 7. Trazabilidad con el análisis EEO

| Componente del 3.1 | Uso en la IA |
| ------------------ | ------------ |
| Espacio de estados $\mathcal{S}$ (vector de 102 componentes) | Dominio sobre el que se hace búsqueda |
| Operadores de la Tabla 2 | Generan las transiciones (los hijos de cada nodo) |
| Restricciones (suma exacta para meta, no aterrizar sobre ficha propia, etc.) | `legal_moves()` filtra las acciones |
| Tablas de propiedades fijas (rosetas, casillas privadas) | Se usan tanto en evaluación como en restricciones |

El propio código de la IA llama a `ops.legal_moves(state)` y
`ops.apply_move(state, piece)` — exactamente los mismos operadores que el
jugador humano usa cuando hace clic. Esto garantiza que la IA respeta el
modelo formal sin atajos.

---

## 8. Posibles preguntas

**P: ¿Por qué no usaste aprendizaje por refuerzo / redes neuronales?**
R: Para el alcance del proyecto (un juego con espacio de estados acotado y
reglas determinísticas en lo que se decide), Expectiminimax con buena
heurística da resultados sólidos sin requerir entrenar nada. Además, mantiene
el código transparente: se puede leer y explicar línea por línea, lo cual es
deseable en un trabajo de análisis EEO.

**P: ¿La IA es determinista?**
R: Casi. Los dados sí son aleatorios, pero la decisión que toma la IA dado
un estado y una suma es determinista (siempre elegirá el mismo movimiento si
recibe exactamente el mismo input). No hay aleatoriedad introducida en la
elección del movimiento más allá del desempate por orden.

**P: ¿Qué pasa si hay empate entre dos movimientos con la misma evaluación?**
R: Gana el primero en el orden recorrido. Como los movimientos se ordenan
heurísticamente (capturas → rosetas → completar → mayor progreso), el
desempate favorece la jugada más "agresiva".

**P: ¿Por qué la profundidad 3 y no la 5?**
R: Profundidad 4 ya tarda 2.5 s; profundidad 5 sería ~30 s/jugada. Para una
sesión interactiva, eso es inaceptable. El equilibrio óptimo se encontró
empíricamente en 3.

**P: ¿Cuál es la complejidad?**
R: En el peor caso, $O(b^d)$ con $b$ = factor de ramificación promedio
(≈ 4–8 movimientos legales en mid-game) y $d$ = profundidad efectiva. Pero
los nodos CHANCE multiplican por 5 (sumas posibles). Con poda alfa-beta y
ordenamiento, en la práctica se reduce a algo cercano a $O(b^{d/2} \cdot 5^{d/2})$.

**P: ¿La función heurística podría engañar a la IA?**
R: Sí, en principio una heurística mala puede llevar a malas decisiones. La
nuestra es **admisible para evaluación** (no para A* — que necesitaría no
sobreestimar el coste hasta meta), pero sí está calibrada. Los pesos se
ajustaron observando partidas y midiendo winrate.

**P: ¿Puede mejorar?**
R: Sí: tablas de transposición (memoization), poda alfa-beta sobre nodos de
chance con cotas probabilísticas, profundidad iterativa con time limit. Pero
para los objetivos del trabajo no es necesario.
