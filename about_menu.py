import pygame
from settings import *

class AboutMenu:
  def __init__(self):
    self.display_surface = pygame.display.get_surface()
    self.active = False

    # --- SCROLLING & CONTENT ---
    self.scroll_y = 0
    self.dragging_scrollbar = False
    self.drag_start_y_offset = 0

    # --- FONT ---
    try:
      self.title_font = pygame.font.Font(FONT, 40)
      self.text_font = pygame.font.Font(FONT, 24)
    except Exception:
      self.title_font = pygame.font.Font(None, 42)
      self.text_font = pygame.font.Font(None, 26)

    # Load images
    try:
      self.board = pygame.image.load('assets/graphics/about/board.png').convert_alpha()
      self.continue_button = pygame.image.load('assets/graphics/option-menu/continue-button.png').convert_alpha()
    except Exception as e:
      self.board = pygame.Surface((700, 500)); self.board.fill((50, 50, 50))
      self.continue_button = pygame.Surface((200, 60)); self.continue_button.fill("blue")

    # --- RECTS ---
    self.board_rect = self.board.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
    self.continue_rect = self.continue_button.get_rect(center=(WINDOW_WIDTH / 2, self.board_rect.bottom - 80))

    # This is the area *inside* the board where text will be visible
    padding_top = 140
    padding_bottom = 140
    padding_x = 60
    self.scrollable_area_rect = self.board_rect.inflate(
        -(padding_x * 2), 
        -(padding_top + padding_bottom)
    )

    # --- SCROLLBAR RECTS & COLORS ---
    self.scroll_track_rect = pygame.Rect(
        self.scrollable_area_rect.right + 10,
        self.scrollable_area_rect.top,
        15, # Width of the scroll track
        self.scrollable_area_rect.height
    )
    self.scroll_thumb_rect = self.scroll_track_rect.copy() # Position/height will be set in draw()
    self.SCROLL_BG_COLOR = (40, 40, 45)
    self.SCROLL_THUMB_COLOR = (100, 100, 110)

    # --- CONTENT TO DISPLAY (Vertical Order) ---
    self.content = {
      'Team': [
        'Pham Nguyen Ngoc Uyen',
        'Pham Thanh Son',
        'Minh Khoa',
        'Tran Tri Dung'
      ],
      'Controls': [
        'Left/Right Arrows - Move',
        'Spacebar - Jump',
        'F - Attack / Interact',
        'Z - Open Inventory',
        'ESC - Pause / Options'
      ],
      'Credits': [
        'Pygame Community',
        'Assets: Treasure Hunters from pixelfrog-assets.itch.io',
        'Music by opengameart.org',
        'Font: PixelifySans',
        'Made with love (and Python)'
      ]
    }
    self.section_order = ['Team', 'Controls', 'Credits']

    # --- PRE-CALCULATE CONTENT HEIGHT & SCROLL ---
    self.line_height = 30
    self.title_height = 45
    self.section_gap = 40
    
    self.content_height = self.calculate_content_height()
    self.max_scroll = max(0, self.content_height - self.scrollable_area_rect.height)


  def calculate_content_height(self):
    current_y = 0
    for section_name in self.section_order:
      current_y += self.title_height
      current_y += len(self.content[section_name]) * self.line_height
      current_y += self.section_gap
    if len(self.section_order) > 0:
      current_y -= self.section_gap
    return current_y

  def draw_text(self, text, pos, font, text_color, stroke_color, align="topleft"):
    stroke_surf = font.render(text, True, stroke_color)
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(**{align: pos})
    stroke_offsets = [(-2, 0), (2, 0), (0, -2), (0, 2)]
    for offset in stroke_offsets:
        stroke_rect = stroke_surf.get_rect(**{align: pos})
        stroke_rect.move_ip(offset)
        self.display_surface.blit(stroke_surf, stroke_rect)
    self.display_surface.blit(text_surf, text_rect)

  def clamp_scroll(self):
    """Ensures self.scroll_y stays within valid bounds."""
    self.scroll_y = max(0, self.scroll_y)
    self.scroll_y = min(self.scroll_y, self.max_scroll)

  def draw(self):
    if not self.active:
      return
      
    # Draw the main board
    self.display_surface.blit(self.board, self.board_rect)

    # --- 1. SET CLIPPING RECT ---
    self.display_surface.set_clip(self.scrollable_area_rect)

    # --- 2. DRAW CONTENT (Vertically) ---
    text_color = "white"
    stroke_color = (51, 50, 61)
    title_color = (231, 205, 141)
    
    start_x = self.scrollable_area_rect.left
    current_y = 0
    for section_name in self.section_order:
      draw_pos_y = self.scrollable_area_rect.top + current_y - self.scroll_y
      self.draw_text(section_name, (start_x, draw_pos_y), self.title_font, title_color, stroke_color)
      current_y += self.title_height
      
      for line in self.content[section_name]:
        draw_pos_y = self.scrollable_area_rect.top + current_y - self.scroll_y
        self.draw_text(line, (start_x + 10, draw_pos_y), self.text_font, text_color, stroke_color)
        current_y += self.line_height
      current_y += self.section_gap

    # --- 3. UNSET CLIPPING RECT ---
    self.display_surface.set_clip(None)

    # --- 4. DRAW SCROLLBAR ---
    if self.max_scroll > 0: # Only draw if scrolling is possible
      # Draw Track
      pygame.draw.rect(self.display_surface, self.SCROLL_BG_COLOR, self.scroll_track_rect, border_radius=5)
      
      # Calculate Thumb height (proportional to content)
      visible_ratio = self.scrollable_area_rect.height / self.content_height
      thumb_height = max(20, self.scroll_track_rect.height * visible_ratio)
      
      # Calculate Thumb position
      scroll_ratio = self.scroll_y / self.max_scroll
      track_travel_range = self.scroll_track_rect.height - thumb_height
      thumb_y = self.scroll_track_rect.top + (scroll_ratio * track_travel_range)
      
      # Update thumb rect and draw
      self.scroll_thumb_rect = pygame.Rect(self.scroll_track_rect.left, thumb_y, self.scroll_track_rect.width, thumb_height)
      pygame.draw.rect(self.display_surface, self.SCROLL_THUMB_COLOR, self.scroll_thumb_rect, border_radius=5)

    # --- 5. DRAW CONTINUE BUTTON ---
    self.display_surface.blit(self.continue_button, self.continue_rect)

  def handle_events(self, events):
    if not self.active:
      return False

    for event in events:
      if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        self.active = False
        self.scroll_y = 0
      
      if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:
          if self.continue_rect.collidepoint(event.pos):
            self.active = False
            self.scroll_y = 0
            return True
          
          # --- Start Scrollbar Drag ---
          elif self.max_scroll > 0 and self.scroll_thumb_rect.collidepoint(event.pos):
            self.dragging_scrollbar = True
            self.drag_start_y_offset = event.pos[1] - self.scroll_thumb_rect.y
            return True
          
          # --- Click on Scroll Track ---
          elif self.max_scroll > 0 and self.scroll_track_rect.collidepoint(event.pos):
            # Move thumb center to mouse y and start dragging
            click_ratio = (event.pos[1] - self.scroll_track_rect.top) / self.scroll_track_rect.height
            self.scroll_y = click_ratio * self.max_scroll
            self.clamp_scroll()
            self.dragging_scrollbar = True
            self.drag_start_y_offset = self.scroll_thumb_rect.height / 2
            return True


      if event.type == pygame.MOUSEBUTTONUP:
        if event.button == 1:
          # --- Stop Scrollbar Drag ---
          self.dragging_scrollbar = False

      if event.type == pygame.MOUSEMOTION:
        # --- Handle Scrollbar Drag ---
        if self.dragging_scrollbar:
          # Get mouse position relative to the track
          mouse_y_in_track = event.pos[1] - self.scroll_track_rect.top - self.drag_start_y_offset
          
          # Calculate scroll ratio
          track_travel_range = self.scroll_track_rect.height - self.scroll_thumb_rect.height
          if track_travel_range > 0:
            scroll_ratio = mouse_y_in_track / track_travel_range
          else:
            scroll_ratio = 0
            
          self.scroll_y = scroll_ratio * self.max_scroll
          self.clamp_scroll()

      if event.type == pygame.MOUSEWHEEL:
        self.scroll_y -= event.y * 30
        self.clamp_scroll()
        
    return False