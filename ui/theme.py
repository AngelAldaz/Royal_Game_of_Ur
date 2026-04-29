"""
Colores y dimensiones del UI.
"""

# Ventana
WIN_W = 1280
WIN_H = 800
FPS = 60

# Colores (RGB)
BG = (28, 28, 35)
PANEL_BG = (20, 20, 28)
TEXT = (235, 235, 240)
TEXT_DIM = (160, 160, 170)
ACCENT = (240, 195, 90)       # dorado
TILE = (60, 60, 75)
TILE_BORDER = (100, 100, 120)
ROSETTE = (180, 90, 60)
ROSETTE_SAFE = (110, 80, 200)

J1_COLOR = (240, 240, 240)    # blanco
J2_COLOR = (40, 40, 50)       # negro
J1_OUTLINE = (200, 200, 210)
J2_OUTLINE = (120, 120, 140)

DICE_BG = (210, 210, 220)
DICE_DOT = (40, 40, 50)
DICE_BORDER = (60, 60, 75)

BTN_BG = (60, 60, 80)
BTN_BG_HOVER = (90, 90, 120)
BTN_TEXT = (240, 240, 245)

OK_GREEN = (90, 200, 120)
WARN_RED = (220, 90, 90)

# Tablero
BOARD_X = 60
BOARD_Y = 200
TILE_SIZE = 80
TILE_GAP = 6

# Layout: el tablero del Ur tiene 3 filas y 8 columnas, con huecos en la fila A y C
# Fila A (J1):  [4][3][2][1] _ _ [14][13]   <- columnas 1..4 y 7..8
# Fila B (com): [5][6][7][8][9][10][11][12] <- columnas 1..8
# Fila C (J2):  [18][17][16][15] _ _ [20][19]
BOARD_ROWS = 3
BOARD_COLS = 8

# Mapeo casilla -> (col_index, row_index) en la cuadricula del tablero.
# row 0 = J1 arriba, row 1 = comun (medio), row 2 = J2 abajo
# Las casillas privadas de J1 estan en su recorrido: 4,3,2,1 (de izq a der) y 14,13
# Recordatorio del layout original del documento:
#         Col1     Col2     Col3     Col4              Col7     Col8
# Fila A   [ 4✿]   [ 3 ]   [ 2 ]   [ 1 ]             [14✿]   [13 ]
# Fila B   [ 5 ]   [ 6 ]   [ 7 ]   [ 8✿]   [ 9 ]    [10 ]   [11 ]   [12 ]
# Fila C   [18✿]   [17 ]   [16 ]   [15 ]             [20✿]   [19 ]
SQUARE_GRID = {
    4: (0, 0),  3: (1, 0),  2: (2, 0),  1: (3, 0),
    14: (6, 0), 13: (7, 0),
    5: (0, 1),  6: (1, 1),  7: (2, 1),  8: (3, 1),
    9: (4, 1), 10: (5, 1), 11: (6, 1), 12: (7, 1),
    18: (0, 2), 17: (1, 2), 16: (2, 2), 15: (3, 2),
    20: (6, 2), 19: (7, 2),
}

# Panel EEO (formula)
PANEL_X = 760
PANEL_Y = 20
PANEL_W = 500
PANEL_H = 760
