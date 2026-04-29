"""
Widgets simples para Pygame: boton, etiqueta. Sin dependencias adicionales.
"""

import pygame
from . import theme as T


class Button:
    def __init__(self, rect, text, callback=None, font=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.font = font
        self.hover = False
        self.enabled = True

    def draw(self, screen):
        color = T.BTN_BG_HOVER if (self.hover and self.enabled) else T.BTN_BG
        if not self.enabled:
            color = (40, 40, 50)
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, T.TILE_BORDER, self.rect, width=2, border_radius=8)
        if self.font:
            text_color = T.BTN_TEXT if self.enabled else T.TEXT_DIM
            txt_surf = self.font.render(self.text, True, text_color)
            tx = self.rect.x + (self.rect.w - txt_surf.get_width()) // 2
            ty = self.rect.y + (self.rect.h - txt_surf.get_height()) // 2
            screen.blit(txt_surf, (tx, ty))

    def handle(self, event):
        if not self.enabled:
            return
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.callback:
                self.callback()


def render_text(screen, text, pos, font, color=T.TEXT):
    screen.blit(font.render(text, True, color), pos)


def render_text_wrapped(screen, text, rect, font, color=T.TEXT, line_spacing=4):
    """Renderiza texto con wrap dentro del rect. Devuelve la y final."""
    rect = pygame.Rect(rect)
    words = text.split(" ")
    space_w = font.size(" ")[0]
    x, y = rect.x, rect.y
    for word in words:
        w, h = font.size(word)
        if x + w > rect.right:
            x = rect.x
            y += h + line_spacing
        screen.blit(font.render(word, True, color), (x, y))
        x += w + space_w
    return y + font.get_height()
