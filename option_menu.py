import pygame
from settings import *

class OptionMenu:
  # Default Volumes
  music_volume = 60
  sfx_volume = 40
  last_music_vol = 60
  last_sfx_vol = 40
  
  dragging_music = False
  dragging_sfx = False

  def __init__(self, state_switch_callback=None, music_track=None, sfx_sounds=None):
    self.display_surface = pygame.display.get_surface()
    self.state_switch_callback = state_switch_callback  # To call main.switch

    # Load images
    self.board = pygame.image.load('assets/graphics/option-menu/option-board.png').convert_alpha()
    self.music_on = pygame.image.load('assets/graphics/option-menu/music-on-button.png').convert_alpha()
    self.music_off = pygame.image.load('assets/graphics/option-menu/music-off-button.png').convert_alpha()
    self.volume_on = pygame.image.load('assets/graphics/option-menu/volume-on-button.png').convert_alpha()
    self.volume_off = pygame.image.load('assets/graphics/option-menu/volume-off-button.png').convert_alpha()
    self.volume_slider = pygame.image.load('assets/graphics/option-menu/volume-slider.png').convert_alpha()
    self.toggle_slider = pygame.image.load('assets/graphics/option-menu/toggle-slider.png').convert_alpha()
    self.continue_button = pygame.image.load('assets/graphics/option-menu/continue-button.png').convert_alpha()
    self.exit_button = pygame.image.load('assets/graphics/option-menu/exit-button.png').convert_alpha()
    self.pause_button = pygame.image.load('assets/graphics/option-menu/pause-button.png').convert_alpha()

    # Rect setup
    self.board_rect = self.board.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
    self.pause_rect = self.pause_button.get_rect(topright=(WINDOW_WIDTH - 20, 20))
    self.button_rects = {}

    # Music + sound settings
    self.music_track = music_track
    self.sfx_sounds = sfx_sounds

    # State
    self.active = False
    self.from_menu = False

    # Font
    try:
      self.font = pygame.font.Font(FONT, 30)
    except FileNotFoundError:
      print(f"ALERT: Cannot find font '{FONT}'. Use defaut font.")
      self.font = pygame.font.Font(None, 32) # Fallback font

    # Apply initial (global) volumes
    self.apply_volume()

  def apply_volume(self):
    """Applies the current GLOBAL volume settings to this instance's tracks."""
    if self.music_track:
      self.music_track.set_volume(OptionMenu.music_volume / 100.0)

    if self.sfx_sounds:
      sfx_vol_float = OptionMenu.sfx_volume / 100.0
      for key, sound in self.sfx_sounds.items():
        if key != 'music':
          sound.set_volume(sfx_vol_float)

  def draw_slider(self, y, volume):
    """Draws slider, knob, and volume number with a stroke."""
    slider_rect = self.volume_slider.get_rect(center=(WINDOW_WIDTH / 2 + 20, y))
    self.display_surface.blit(self.volume_slider, slider_rect)

    knob_x = slider_rect.left + (volume / 100) * slider_rect.width
    knob_rect = self.toggle_slider.get_rect(center=(knob_x, y))
    self.display_surface.blit(self.toggle_slider, knob_rect)

    # Draw text with stroke
    vol_str = str(int(volume))
    stroke_color = (51, 50, 61)
    text_color = (231, 205, 141)

    base_pos_midleft = (slider_rect.right + 15, slider_rect.centery)

    # Stroke
    stroke_offsets = [(-2, 0), (2, 0), (0, -2), (0, 2)]
    for offset in stroke_offsets:
      stroke_surf = self.font.render(vol_str, True, stroke_color)
      stroke_rect = stroke_surf.get_rect(midleft=base_pos_midleft)
      stroke_rect.move_ip(offset)
      self.display_surface.blit(stroke_surf, stroke_rect)

    # Main text
    text_surf = self.font.render(vol_str, True, text_color)
    text_rect = text_surf.get_rect(midleft=base_pos_midleft)
    self.display_surface.blit(text_surf, text_rect)

    return slider_rect, knob_rect

  def draw_buttons(self):
    """Draws the menu layout."""
    self.display_surface.blit(self.board, self.board_rect)

    # SFX Row
    sfx_img = self.volume_on if OptionMenu.sfx_volume > 0 else self.volume_off
    sfx_rect = sfx_img.get_rect(center=(WINDOW_WIDTH / 2 - 150, self.board_rect.centery - 50))
    self.display_surface.blit(sfx_img, sfx_rect)
    sfx_slider, sfx_knob = self.draw_slider(sfx_rect.centery, OptionMenu.sfx_volume)

    # Music Row
    music_img = self.music_on if OptionMenu.music_volume > 0 else self.music_off
    music_rect = music_img.get_rect(center=(WINDOW_WIDTH / 2 - 150, self.board_rect.centery + 50))
    self.display_surface.blit(music_img, music_rect)
    music_slider, music_knob = self.draw_slider(music_rect.centery, OptionMenu.music_volume)

    # Buttons Row
    cont_rect = self.continue_button.get_rect(center=(WINDOW_WIDTH / 2 - 100, self.board_rect.centery + 130))
    exit_rect = self.exit_button.get_rect(center=(WINDOW_WIDTH / 2 + 100, self.board_rect.centery + 130))
    self.display_surface.blit(self.continue_button, cont_rect)
    self.display_surface.blit(self.exit_button, exit_rect)

    return {
      "music_btn": music_rect, "sfx_btn": sfx_rect,
      "music_slider": music_slider, "sfx_slider": sfx_slider,
      "music_knob": music_knob, "sfx_knob": sfx_knob,
      "continue": cont_rect, "exit": exit_rect
    }

  def draw_pause_button(self):
    self.display_surface.blit(self.pause_button, self.pause_rect)
    return self.pause_rect

  def handle_events(self, events):
    """Handles input. Returns 'menu' signal if needed."""
    click_consumed = False
    for event in events:
      if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        pos = pygame.mouse.get_pos()

        if self.active and self.button_rects: # Menu is open
          click_consumed = True
          if self.button_rects["music_knob"].collidepoint(pos):
            OptionMenu.dragging_music = True
          elif self.button_rects["sfx_knob"].collidepoint(pos):
            OptionMenu.dragging_sfx = True

          for name, rect in self.button_rects.items():
            if rect.collidepoint(pos):
              if name == "music_btn":
                if OptionMenu.music_volume > 0: OptionMenu.last_music_vol = OptionMenu.music_volume; OptionMenu.music_volume = 0
                else: OptionMenu.music_volume = OptionMenu.last_music_vol
                self.apply_volume()
              elif name == "sfx_btn":
                if OptionMenu.sfx_volume > 0: OptionMenu.last_sfx_vol = OptionMenu.sfx_volume; OptionMenu.sfx_volume = 0
                else: OptionMenu.sfx_volume = OptionMenu.last_sfx_vol
                self.apply_volume()
              elif name == "continue":
                self.active = False
              elif name == "exit":
                if self.from_menu: pygame.quit(); import sys; sys.exit()
                else:
                  self.active = False
                  if self.state_switch_callback:
                    self.state_switch_callback(action='menu'); return 'menu'
              elif name == "music_slider":
                rel_x = pos[0] - rect.left; OptionMenu.music_volume = min(100, max(0, int(rel_x / rect.width * 100)))
                if OptionMenu.music_volume > 0: OptionMenu.last_music_vol = OptionMenu.music_volume
                self.apply_volume(); OptionMenu.dragging_music = True
              elif name == "sfx_slider":
                rel_x = pos[0] - rect.left; OptionMenu.sfx_volume = min(100, max(0, int(rel_x / rect.width * 100)))
                if OptionMenu.sfx_volume > 0: OptionMenu.last_sfx_vol = OptionMenu.sfx_volume
                self.apply_volume(); OptionMenu.dragging_sfx = True

        elif not self.active and not self.from_menu: # Menu closed, in game
          if self.pause_rect.collidepoint(pos):
            self.active = True # Open menu
            click_consumed = True

      elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        OptionMenu.dragging_music = False; OptionMenu.dragging_sfx = False

      elif event.type == pygame.MOUSEMOTION:
        pos = pygame.mouse.get_pos()
        if OptionMenu.dragging_music and self.button_rects:
          rect = self.button_rects["music_slider"]; rel_x = pos[0] - rect.left
          OptionMenu.music_volume = min(100, max(0, int(rel_x / rect.width * 100)))
          if OptionMenu.music_volume > 0: OptionMenu.last_music_vol = OptionMenu.music_volume
          self.apply_volume()
        if OptionMenu.dragging_sfx and self.button_rects:
          rect = self.button_rects["sfx_slider"]; rel_x = pos[0] - rect.left
          OptionMenu.sfx_volume = min(100, max(0, int(rel_x / rect.width * 100)))
          if OptionMenu.sfx_volume > 0: OptionMenu.last_sfx_vol = OptionMenu.sfx_volume
          self.apply_volume()

      elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        if self.from_menu: # Only toggle ESC in main menu
          self.active = not self.active
      
      if click_consumed:
        return True

    return False

  def draw(self):
    """Draws the active menu OR the pause button."""
    if self.active:
      self.button_rects = self.draw_buttons()
    elif not self.from_menu: # Only draw pause button if in game
      self.draw_pause_button()