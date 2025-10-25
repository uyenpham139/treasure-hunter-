import pygame, sys
from pygame.image import load
from settings import *
from option_menu import OptionMenu
from about_menu import AboutMenu

class MainMenu:
  def __init__(self, music_track, sfx_sounds):
    self.display = pygame.display.get_surface()
    self.font = pygame.font.Font(FONT, 48)
    self.bg = load('assets/graphics/menu/bg.png').convert_alpha()
    self.editor_button_img = load('assets/graphics/menu/small-button.png').convert_alpha()
    self.button_img = load('assets/graphics/menu/button.png').convert_alpha()

    # Main buttons
    self.buttons = {
      "New Game": pygame.Rect(WINDOW_WIDTH / 2 - 150, 300, 300, 70),
      "Editor": pygame.Rect(WINDOW_WIDTH - self.editor_button_img.get_width() - 20, 20, 56, 56),
      "About": pygame.Rect(WINDOW_WIDTH / 2 - 150, 400, 300, 70), 
      "Options": pygame.Rect(WINDOW_WIDTH / 2 - 150, 500, 300, 70),
      "Quit": pygame.Rect(WINDOW_WIDTH / 2 - 150, 600, 300, 70),
    }

    # Create OptionMenu instance, passing the audio tracks
    self.option_menu = OptionMenu(music_track=music_track, sfx_sounds=sfx_sounds)
    self.option_menu.from_menu = True
    self.option_menu.active = False
    
    self.about_menu = AboutMenu()
    self.about_menu.active = False

  def draw_button(self, text, rect):
    stroke_color = (51, 50, 61)
    text_color = (255, 255, 255)

    # --- FIX 2: The image MUST be drawn FIRST, as the background ---
    if text == "Editor":
        image = self.editor_button_img
    else:
        image = self.button_img
    self.display.blit(image, rect)

    if text != "Editor":
        center_pos = (rect.center[0], rect.center[1] - 8)
        stroke_surf = self.font.render(text, True, stroke_color)
        
        # Draw the 4 stroke outlines
        stroke_offsets = [(-2, 0), (2, 0), (0, -2), (0, 2)]
        for offset in stroke_offsets:
            stroke_rect = stroke_surf.get_rect(center=center_pos)
            stroke_rect.move_ip(offset) 
            self.display.blit(stroke_surf, stroke_rect)
            
        txt_surf = self.font.render(text, True, text_color)
        self.display.blit(txt_surf, txt_surf.get_rect(center=center_pos))

  def run(self):
    while True:
      # --- 1. HANDLE EVENTS ---
      events = pygame.event.get()

      # Pass all events to option menu handler
      option_consumed_click = self.option_menu.handle_events(events)
      about_consumed_click = self.about_menu.handle_events(events)

      for event in events:
        if event.type == pygame.QUIT:
          pygame.quit()
          sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
          if option_consumed_click or about_consumed_click:
            continue
          
          pos = pygame.mouse.get_pos()
          # Only respond to main buttons if the option menu isn't active
          if not self.option_menu.active and not self.about_menu.active:
            for name, rect in self.buttons.items():
              if rect.collidepoint(pos):
                if name == "New Game":
                  return "new_game"
                elif name == "Editor":
                  return "editor"
                elif name == "About":
                  self.about_menu.active = True
                elif name == "Options":
                  # Use the new .active attribute directly
                  self.option_menu.active = True
                elif name == "Quit":
                  return "quit"

      # --- 2. DRAWING ---
      self.display.blit(self.bg, (0, 0))

      # Draw main menu buttons only when options not visible
      if not self.option_menu.active and not self.about_menu.active:
        for name, rect in self.buttons.items():
          self.draw_button(name, rect)

      # Draw other menus
      self.option_menu.draw()
      self.about_menu.draw()

      pygame.display.update()