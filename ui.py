# Small UI helpers for buttons and simple labels.
import pygame
from settings import BLACK, GRAY, WHITE

def draw_button(surface, rect, text, font, bg=GRAY, fg=BLACK):
    pygame.draw.rect(surface, bg, rect)
    pygame.draw.rect(surface, BLACK, rect, 2)
    label = font.render(text, True, fg)
    surface.blit(label, (rect.x + (rect.width - label.get_width())//2,
                         rect.y + (rect.height - label.get_height())//2))

def draw_title(surface, title, subtitle, font_title, font_sub, y_offset=40):
    w = surface.get_width()
    title_surf = font_title.render(title, True, BLACK)
    sub_surf = font_sub.render(subtitle, True, BLACK)
    surface.blit(title_surf, (w//2 - title_surf.get_width()//2, y_offset))
    surface.blit(sub_surf, (w//2 - sub_surf.get_width()//2, y_offset + title_surf.get_height() + 8))
