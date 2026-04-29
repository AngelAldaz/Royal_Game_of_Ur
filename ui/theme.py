"""
Colores y dimensiones del UI.
Paleta inspirada en el tablero original de Ur (madera y lapislázuli).
"""

# Ventana
WIN_W = 1280
WIN_H = 800
FPS = 60

# Colores (RGB)
BG = (28, 22, 18)               # marrón muy oscuro (fondo)
BG_GRAD_TOP = (38, 30, 24)
BG_GRAD_BOT = (18, 14, 10)
PANEL_BG = (24, 20, 16)
PANEL_BORDER = (90, 75, 50)
TEXT = (240, 230, 210)
TEXT_DIM = (170, 155, 130)
ACCENT = (245, 200, 100)        # dorado
ACCENT_DIM = (160, 130, 70)

# Tablero (madera oscura)
BOARD_BG = (62, 42, 28)
BOARD_BORDER = (110, 75, 40)
TILE = (88, 65, 42)             # cuadros normales (madera media)
TILE_BORDER = (140, 105, 70)
TILE_HOVER = (115, 92, 62)

# Rosetas — color lapislázuli (azul oscuro con motas)
ROSETTE = (60, 90, 150)
ROSETTE_DOT = (240, 200, 110)
ROSETTE_BORDER = (100, 140, 200)
ROSETTE_SAFE = (140, 90, 200)   # roseta 8 — púrpura para distinguirla
ROSETTE_SAFE_DOT = (255, 220, 130)

# Fichas
J1_COLOR = (245, 240, 225)      # blanco hueso
J1_HIGHLIGHT = (255, 255, 245)
J1_SHADOW = (180, 170, 150)
J1_NUMBER = (60, 40, 25)

J2_COLOR = (35, 28, 22)         # negro mate
J2_HIGHLIGHT = (75, 60, 48)
J2_SHADOW = (15, 10, 8)
J2_NUMBER = (245, 225, 180)

# Dados
DICE_BG = (220, 215, 200)
DICE_BG_TOP = (240, 235, 220)
DICE_DOT = (35, 28, 22)
DICE_BORDER = (110, 90, 60)

# Botones
BTN_BG = (70, 55, 35)
BTN_BG_HOVER = (110, 85, 50)
BTN_BG_DISABLED = (40, 35, 28)
BTN_BORDER = (140, 105, 70)
BTN_TEXT = (245, 230, 200)
BTN_TEXT_DISABLED = (110, 100, 85)

# Estados
OK_GREEN = (130, 220, 140)
WARN_RED = (220, 90, 90)
SELECTION = (255, 220, 110)

# Layout
BOARD_X = 100
BOARD_Y = 220
TILE_SIZE = 72
TILE_GAP = 6

# Layout: el tablero del Ur tiene 3 filas y 8 columnas, con huecos en la fila A y C
BOARD_ROWS = 3
BOARD_COLS = 8

# Mapeo casilla -> (col_index, row_index) en la cuadricula del tablero.
# row 0 = J1 arriba, row 1 = comun (medio), row 2 = J2 abajo
SQUARE_GRID = {
    4: (0, 0),  3: (1, 0),  2: (2, 0),  1: (3, 0),
    14: (6, 0), 13: (7, 0),
    5: (0, 1),  6: (1, 1),  7: (2, 1),  8: (3, 1),
    9: (4, 1), 10: (5, 1), 11: (6, 1), 12: (7, 1),
    18: (0, 2), 17: (1, 2), 16: (2, 2), 15: (3, 2),
    20: (6, 2), 19: (7, 2),
}

# Panel EEO
PANEL_X = 800
PANEL_Y = 20
PANEL_W = 460
PANEL_H = 760
