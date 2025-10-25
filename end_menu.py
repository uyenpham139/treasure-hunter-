# end_menu.py
import pygame
from settings import *
from pygame.math import Vector2 as vector

class EndMenu:
    def __init__(self, coin_counts, switch_to_menu_callback, background_level=None):
        self.display_surface = pygame.display.get_surface()
        self.coin_counts = coin_counts
        self.switch_to_menu = switch_to_menu_callback # This will be main.switch
        self.background_level = background_level
        
        # Load assets
        self.board_surf = pygame.image.load('assets/graphics/end-menu/board.png').convert_alpha()
        self.silver_surf = pygame.image.load('assets/graphics/end-menu/silver.png').convert_alpha()
        self.gold_surf = pygame.image.load('assets/graphics/end-menu/gold.png').convert_alpha()
        self.diamond_surf = pygame.image.load('assets/graphics/end-menu/diamond.png').convert_alpha()
        self.menu_button_surf = pygame.image.load('assets/graphics/end-menu/menu-button.png').convert_alpha()

        # Font
        try:
            self.font = pygame.font.Font(FONT, 30)
        except Exception:
            self.font = pygame.font.Font(None, 32)
        
        # Rects
        self.board_rect = self.board_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        
        # Position button at bottom-center of the board
        self.menu_button_rect = self.menu_button_surf.get_rect(midbottom=self.board_rect.midbottom + vector(0, -40))

        self.active = True

    def draw_text(self, text, pos, color=(80, 80, 80), stroke_color='#ffffff'):
        # Simple stroke effect
        stroke_offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for offset in stroke_offsets:
            stroke_surf = self.font.render(text, True, stroke_color)
            stroke_rect = stroke_surf.get_rect(midleft=pos)
            stroke_rect.move_ip(offset)
            self.display_surface.blit(stroke_surf, stroke_rect)

        # Main text
        text_surf = self.font.render(text, True, color)
        text_rect = text_surf.get_rect(midleft=pos)
        self.display_surface.blit(text_surf, text_rect)

    def run(self):
        if not self.active:
            return 'menu'

        # Event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); import sys; sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.menu_button_rect.collidepoint(event.pos):
                    self.active = False
                    return 'menu'

        # Drawing
        if self.background_level:
            try:
                self.background_level.all_sprites.custom_draw(self.background_level.player)
                self.background_level.draw_player_health_bar()
                self.background_level.draw_coin_hud()
                self.background_level.inventory.display() 
            except Exception as e:
                print(f"Error drawing background level: {e}")
                self.display_surface.fill(SKY_COLOR)
        else:
            self.display_surface.fill(SKY_COLOR)
        
        # Draw board
        self.display_surface.blit(self.board_surf, self.board_rect)

        center_x = self.board_rect.centerx
        center_y = self.board_rect.centery + 30 # Slightly below center
        spacing = 100 # Horizontal space between items
        text_offset = vector(10, 0) # Space between icon and text

        # Silver
        silver_pos = (center_x - spacing - 60, center_y)
        silver_rect = self.silver_surf.get_rect(center=silver_pos)
        self.display_surface.blit(self.silver_surf, silver_rect)
        self.draw_text(f"x {self.coin_counts.get('silver', 0)}", silver_rect.midright + text_offset)

        # Gold
        gold_pos = (center_x - 30, center_y)
        gold_rect = self.gold_surf.get_rect(center=gold_pos)
        self.display_surface.blit(self.gold_surf, gold_rect)
        self.draw_text(f"x {self.coin_counts.get('gold', 0)}", gold_rect.midright + text_offset)

        # Diamond
        diamond_pos = (center_x + spacing - 10, center_y)
        diamond_rect = self.diamond_surf.get_rect(center=diamond_pos)
        self.display_surface.blit(self.diamond_surf, diamond_rect)
        self.draw_text(f"x {self.coin_counts.get('diamond', 0)}", diamond_rect.midright + text_offset)

        # Draw menu button
        self.display_surface.blit(self.menu_button_surf, self.menu_button_rect)

        pygame.display.update()
        return None 