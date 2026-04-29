# The Royal Game of Ur — Implementación EEO

Implementación en Python + Pygame del Royal Game of Ur, basada directamente en el
análisis EEO desarrollado en el documento 3.1.

Características:
- 2 modos de juego: **Humano vs Humano** y **Humano vs IA**.
- IA basada en **Expectiminimax** (profundidad 2) con heurística que considera
  rosetas, capturas, progreso y vulnerabilidad en la zona compartida.
- Panel lateral en tiempo real con el **vector de estado EEO completo**:
  jugadores, fichas, dados, tablero y casillas.
- Mensajes del último operador aplicado.

## Requisitos

- Python 3.10 o superior
- Pygame 2.5+

## Instalación

1. Instalar Python desde https://www.python.org/downloads/ (marcar "Add Python to PATH").
2. Abrir terminal en la carpeta del proyecto y ejecutar:

   ```
   pip install -r requirements.txt
   ```

## Cómo ejecutar

```
python main.py
```

## Controles

- **Lanzar dados**: botón en la esquina inferior izquierda.
- **Mover ficha**: hacer click sobre la ficha que quieres mover (en reserva o en el tablero).
  Las casillas destino válidas se resaltan en verde.
- **Pasar turno**: cuando los dados suman 0 o no hay movimientos legales.

## Estructura del proyecto

```
Ur-Game/
├── main.py               Entrada y loop principal
├── requirements.txt
├── README.md
├── game/
│   ├── constants.py      Caminos, rosetas, identificadores (Tabla 1)
│   ├── state.py          Vector de estado (Piece, GameState)
│   ├── operators.py      Los 8 operadores (Tabla 2)
│   └── ai.py             Expectiminimax + heurística
└── ui/
    ├── theme.py          Colores y dimensiones
    ├── widgets.py        Botones, etiquetas
    ├── board_view.py     Render tablero, fichas, reservas
    ├── dice_view.py      Render dados
    ├── eeo_panel.py      Panel del vector EEO
    └── menus.py          Menú principal y fin de juego
```

## Mapeo con el análisis EEO 3.1

| EEO 3.1                          | Implementación                                    |
| -------------------------------- | ------------------------------------------------- |
| Tabla 1 — Entidades y atributos  | `game/state.py`, `game/constants.py`              |
| Vector de estado de 102 comp.    | Clase `GameState` + panel `ui/eeo_panel.py`       |
| Tabla 2 — Operadores y reglas    | `game/operators.py` (un operador por función)     |
| Espacio de Estados               | Cada turno aplica un operador → genera transición |
