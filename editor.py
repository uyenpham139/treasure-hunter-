import pygame, sys, os, json 
from pygame.math import Vector2 as vector
from pygame.mouse import get_pressed as mouse_buttons
from pygame.mouse import get_pos as mouse_pos
from pygame.image import load

from random import choice, randint

from settings import *
from support import *
from editor_menu import EditorMenu
from timer import Timer


class Editor:
	def __init__(self, land_tiles, switch, level_grid=None):
		
		# main setup 
		self.display_surface = pygame.display.get_surface()
		self.canvas_data = {}
		self.switch = switch

		# imports 
		self.land_tiles = land_tiles
		self.imports()

		# clouds
		self.current_clouds = []
		self.cloud_surf = import_folder('assets/graphics/clouds')
		self.cloud_timer = pygame.USEREVENT + 1
		pygame.time.set_timer(self.cloud_timer, 2000)
		self.startup_clouds()

		# navigation
		self.origin = vector()
		self.pan_active = False
		self.pan_offset = vector()

		# support lines 
		self.support_line_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
		self.support_line_surf.set_colorkey('green')
		self.support_line_surf.set_alpha(30)

		# selection
		self.selection_index = 2
		self.last_selected_cell = None

		# menu 
		self.menu = EditorMenu()

		# objects
		self.canvas_objects = pygame.sprite.Group()
		self.foreground = pygame.sprite.Group()
		self.background = pygame.sprite.Group()
		self.object_drag_active = False
		self.object_timer = Timer(400)

		if level_grid:
			self.load_from_grid(level_grid)
		else:
			# Player
			CanvasObject(
				pos = (200, WINDOW_HEIGHT / 2), 
				frames = self.animations[0]['frames'],
				tile_id =  0, 
				origin = self.origin, 
				group = [self.canvas_objects, self.foreground])

			# sky
			self.sky_handle = CanvasObject(
				pos = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2),
				frames = [self.sky_handle_surf],
				tile_id = 1,
				origin = self.origin,
				group = [self.canvas_objects, self.background])

		# music
		self.editor_music = pygame.mixer.Sound('assets/audio/Explorer.ogg')
		self.editor_music.set_volume(0.4)
		# Note: Music starts in Main.switch(grid=None)

	def load_from_grid(self, grid):
		if 'terrain' in grid:
			for pos, terrain_string in grid['terrain'].items():
				cell_pos = (pos[0] // TILE_SIZE, pos[1] // TILE_SIZE)
				tile_id = 2 
				if cell_pos in self.canvas_data:
					self.canvas_data[cell_pos].add_id(tile_id)
				else:
					self.canvas_data[cell_pos] = CanvasTile(tile_id)

		# Handle water tiles (which always have an ID of 3)
		if 'water' in grid:
			for pos, water_type in grid['water'].items():
				cell_pos = (pos[0] // TILE_SIZE, pos[1] // TILE_SIZE)
				tile_id = 3
				if cell_pos in self.canvas_data:
					self.canvas_data[cell_pos].add_id(tile_id)
				else:
					self.canvas_data[cell_pos] = CanvasTile(tile_id)

		# Handle coins and enemies (where the JSON value IS the correct tile_id)
		for layer_name in ('coins', 'enemies'):
			if layer_name in grid:
				for pos, tile_id in grid[layer_name].items():
					cell_pos = (pos[0] // TILE_SIZE, pos[1] // TILE_SIZE)
					if cell_pos in self.canvas_data:
						self.canvas_data[cell_pos].add_id(tile_id)
					else:
						self.canvas_data[cell_pos] = CanvasTile(tile_id)
    
		# Items
		if 'items' in grid:
			for pos, tile_id in grid['items'].items():
				cell_pos = (pos[0] // TILE_SIZE, pos[1] // TILE_SIZE)
				if cell_pos in self.canvas_data:
					self.canvas_data[cell_pos].add_id(tile_id)
				else:
					self.canvas_data[cell_pos] = CanvasTile(tile_id)

		# 2. Load all object-based elements into canvas_objects
		for layer_name in ('fg objects', 'bg palms'):
			if layer_name in grid:
				for pos, tile_id in grid[layer_name].items():
					groups = [self.canvas_objects, self.background] if EDITOR_DATA[tile_id]['style'] == 'palm_bg' else [self.canvas_objects, self.foreground]
					
					# Determine which frames to use based on the object's ID
					if tile_id == 1: # Special case for the sky handle
						frames_to_use = [self.sky_handle_surf]
					else: # All other animated objects
						frames_to_use = self.animations[tile_id]['frames']

					obj = CanvasObject(
						pos = pos,
						frames = frames_to_use, # Use the correct frames
						tile_id = tile_id,
						origin = self.origin,
						group = groups,
      			anchor='topleft')
					
					if tile_id == 1:
						self.sky_handle = obj

		# 3. Re-run the neighbor check on all tiles to correctly draw the autotiles
		for cell in self.canvas_data:
			self.check_neighbors(cell)
   
	# support
 
	def get_current_cell(self, obj = None):
		distance_to_origin = vector(mouse_pos()) - self.origin if not obj else vector(obj.distance_to_origin) - self.origin

		if distance_to_origin.x > 0:
			col = int(distance_to_origin.x / TILE_SIZE)
		else:
			col = int(distance_to_origin.x / TILE_SIZE) - 1

		if distance_to_origin.y > 0:
			row = int(distance_to_origin.y / TILE_SIZE)
		else:
			row = int(distance_to_origin.y / TILE_SIZE) - 1

		return col, row

	def check_neighbors(self, cell_pos):
		cluster_size = 3
		local_cluster = [
			(cell_pos[0] + col - int(cluster_size / 2), cell_pos[1] + row - int(cluster_size / 2)) 
			for col in range(cluster_size) 
			for row in range(cluster_size)]

		# check neighbors
		for cell in local_cluster:
			if cell in self.canvas_data:
				self.canvas_data[cell].terrain_neighbors = []
				self.canvas_data[cell].water_on_top = False
				for name, side in NEIGHBOR_DIRECTIONS.items():
					neighbor_cell = (cell[0] + side[0],cell[1] + side[1])

					if neighbor_cell in self.canvas_data:
					# water top neighbor
						if self.canvas_data[neighbor_cell].has_water and self.canvas_data[cell].has_water and name == 'A':
							self.canvas_data[cell].water_on_top = True

					# terrain neighbors
						if self.canvas_data[neighbor_cell].has_terrain:
							self.canvas_data[cell].terrain_neighbors.append(name)

	def imports(self):
		self.water_bottom = load('assets/graphics/terrain/water/water_bottom.png').convert_alpha()
		self.sky_handle_surf = load('assets/graphics/cursors/handle.png').convert_alpha()

		# animations
		self.animations = {}
		for key, value in EDITOR_DATA.items():
			if value['graphics']:
				graphics = import_folder(value['graphics'])
				self.animations[key] = {
					'frame index': 0,
					'frames': graphics,
					'length': len(graphics)
				}

		# preview
		self.preview_surfs = {key: load(value['preview']) for key, value in EDITOR_DATA.items() if value['preview']}

	def animation_update(self, dt):
		for value in self.animations.values():
			value['frame index'] += ANIMATION_SPEED * dt
			if value['frame index'] >= value['length']:
				value['frame index'] = 0

	def mouse_on_object(self):
		for sprite in self.canvas_objects:
			if sprite.rect.collidepoint(mouse_pos()):
				return sprite

	def create_grid(self):
		for tile in self.canvas_data.values():
			tile.objects = []

		for obj in self.canvas_objects:
			current_cell = self.get_current_cell(obj)
			offset = vector(obj.distance_to_origin) - (vector(current_cell) * TILE_SIZE)

			if current_cell in self.canvas_data: # tile exists already
				self.canvas_data[current_cell].add_id(obj.tile_id, offset)
			else: # no tile exists yet 
				self.canvas_data[current_cell] = CanvasTile(obj.tile_id, offset)

		# create an empty grid
		layers = {
			'water': {},
			'bg palms': {},
			'terrain': {}, 
			'enemies': {},
			'coins': {}, 
			'fg objects': {},
			'items': {},
		}

		# grid offset 
		if not self.canvas_data:
			return layers
			
		left = sorted(self.canvas_data.keys(), key = lambda tile: tile[0])[0][0]
		top = sorted(self.canvas_data.keys(), key = lambda tile: tile[1])[0][1]

		# fill the grid
		for tile_pos, tile in self.canvas_data.items():
			row_adjusted = tile_pos[1] - top
			col_adjusted = tile_pos[0] - left
			x = col_adjusted * TILE_SIZE
			y = row_adjusted * TILE_SIZE

			if tile.has_water:
				layers['water'][(x,y)] = tile.get_water()

			if tile.has_terrain:
				terrain_string = tile.get_terrain()
				layers['terrain'][(x,y)] = terrain_string if terrain_string in self.land_tiles else 'X'

			if tile.coin:
				layers['coins'][(x + TILE_SIZE // 2,y + TILE_SIZE // 2)] = tile.coin

			if tile.enemy:
				layers['enemies'][(x,y)] = tile.enemy
    
			if tile.item:
				layers['items'][(x, y)] = tile.item

			if tile.objects: # (obj, offset)
				for obj, offset in tile.objects:
					if obj in [key for key, value in EDITOR_DATA.items() if value['style'] == 'palm_bg']: # bg palm
						layers['bg palms'][(int(x + offset.x), int(y + offset.y))] = obj
					else: # fg objects
						layers['fg objects'][(int(x + offset.x), int(y + offset.y))] = obj

		return layers

	def save_level_data(self, grid_data):
		# Convert tuple keys to string keys for JSON saving.
		serializable_grid = {}
		for layer_name, layer_data in grid_data.items():
			if layer_data:
				serializable_grid[layer_name] = {f"{k[0]},{k[1]}": v for k, v in layer_data.items()}

		# Define save path: 'data/saved_level_grid.json' 
		filename = "saved_level_grid.json"
		os.makedirs("data", exist_ok=True)
		save_path = os.path.join("data", filename)
		
		try:
			with open(save_path, 'w') as f:
				json.dump(serializable_grid, f, indent=4)
			print(f"✅ Level grid saved to {save_path}")
		except Exception as e:
			print(f"Error saving level: {e}")

	# input
	def event_loop(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			
			if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
				# 1. Create the grid from the current canvas objects
				grid = self.create_grid()
				# 2. Save the grid persistently
				self.save_level_data(grid)
				# 3. Switch back to the Menu, carrying the grid data
				self.switch(grid=grid, action='menu') 
				self.editor_music.stop()

			self.pan_input(event)
			self.selection_hotkeys(event)
			self.menu_click(event)

			self.object_drag(event)
			
			self.canvas_add()
			self.canvas_remove()

			self.create_clouds(event)

	def pan_input(self, event): 
		# middle mouse button pressed / released 
		if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[1]:
			self.pan_active = True
			self.pan_offset = vector(mouse_pos()) - self.origin

		if not mouse_buttons()[1]:
			self.pan_active = False

		# mouse wheel 
		if event.type == pygame.MOUSEWHEEL:
			if pygame.key.get_pressed()[pygame.K_LCTRL]:
				self.origin.y -= event.y * 50
			else:
				self.origin.x -= event.y * 50
			for sprite in self.canvas_objects:
				sprite.pan_pos(self.origin)

		# panning update
		if self.pan_active:
			self.origin = vector(mouse_pos()) - self.pan_offset

			for sprite in self.canvas_objects:
				sprite.pan_pos(self.origin)

	def selection_hotkeys(self, event):
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_RIGHT:
				self.selection_index += 1
			if event.key == pygame.K_LEFT:
				self.selection_index -= 1
		self.selection_index = max(2,min(self.selection_index, len(EDITOR_DATA) - 1))

	def menu_click(self, event):
		if event.type == pygame.MOUSEBUTTONDOWN and self.menu.rect.collidepoint(mouse_pos()):
			new_index = self.menu.click(mouse_pos(), mouse_buttons())
			self.selection_index = new_index if new_index else self.selection_index

	def canvas_add(self):
		if mouse_buttons()[0] and not self.menu.rect.collidepoint(mouse_pos()) and not self.object_drag_active:
			current_cell = self.get_current_cell()
			if EDITOR_DATA[self.selection_index]['type'] == 'tile':

				if current_cell != self.last_selected_cell:

					if current_cell in self.canvas_data:
						self.canvas_data[current_cell].add_id(self.selection_index)
					else:
						self.canvas_data[current_cell] = CanvasTile(self.selection_index)
			
					self.check_neighbors(current_cell)
					self.last_selected_cell = current_cell
			else: # object
				if not self.object_timer.active:
					groups = [self.canvas_objects, self.background] if EDITOR_DATA[self.selection_index]['style'] == 'palm_bg' else [self.canvas_objects, self.foreground]
					CanvasObject(
						pos = mouse_pos(),
						frames = self.animations[self.selection_index]['frames'],
						tile_id = self.selection_index,
						origin = self.origin,
						group = groups)
					self.object_timer.activate()

	def canvas_remove(self):
		if mouse_buttons()[2] and not self.menu.rect.collidepoint(mouse_pos()):

			# delete object
			selected_object = self.mouse_on_object()
			if selected_object:
				if EDITOR_DATA[selected_object.tile_id]['style'] not in ('player', 'sky'):
					selected_object.kill()

			# delete tiles
			if self.canvas_data:
				current_cell = self.get_current_cell()
				if current_cell in self.canvas_data:
					self.canvas_data[current_cell].remove_id(self.selection_index)

					if self.canvas_data[current_cell].is_empty:
						del self.canvas_data[current_cell]
					self.check_neighbors(current_cell)

	def object_drag(self, event):
		if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[0]:
			for sprite in self.canvas_objects:
				if sprite.rect.collidepoint(event.pos):
					sprite.start_drag()
					self.object_drag_active = True

		if event.type == pygame.MOUSEBUTTONUP and self.object_drag_active:
			for sprite in self.canvas_objects:
				if sprite.selected:
					sprite.drag_end(self.origin)
					self.object_drag_active = False

	# drawing 
	def draw_tile_lines(self):
		cols = WINDOW_WIDTH // TILE_SIZE
		rows = WINDOW_HEIGHT// TILE_SIZE

		origin_offset = vector(
			x = self.origin.x - int(self.origin.x / TILE_SIZE) * TILE_SIZE,
			y = self.origin.y - int(self.origin.y / TILE_SIZE) * TILE_SIZE)

		self.support_line_surf.fill('green')

		for col in range(cols + 1):
			x = origin_offset.x + col * TILE_SIZE
			pygame.draw.line(self.display_surface,LINE_COLOR, (x,0), (x,WINDOW_HEIGHT))

		for row in range(rows + 1):
			y = origin_offset.y + row * TILE_SIZE
			pygame.draw.line(self.display_surface,LINE_COLOR, (0,y), (WINDOW_WIDTH,y))

		self.display_surface.blit(self.support_line_surf,(0,0))

	def draw_level(self):
		self.background.draw(self.display_surface)
		for cell_pos, tile in self.canvas_data.items():
			pos = self.origin + vector(cell_pos) * TILE_SIZE

			# water
			if tile.has_water:
				if tile.water_on_top:
					self.display_surface.blit(self.water_bottom, pos)
				else:
					frames = self.animations[3]['frames']
					index  = int(self.animations[3]['frame index'])
					surf = frames[index]
					self.display_surface.blit(surf, pos)

			if tile.has_terrain:
				terrain_string = ''.join(tile.terrain_neighbors)
				terrain_style = terrain_string if terrain_string in self.land_tiles else 'X'
				self.display_surface.blit(self.land_tiles[terrain_style], pos)

			# coins
			if tile.coin:
				frames = self.animations[tile.coin]['frames']
				index = int(self.animations[tile.coin]['frame index'])
				surf = frames[index]
				rect = surf.get_rect(center = (pos[0] + TILE_SIZE // 2, pos[1]+ TILE_SIZE // 2))
				self.display_surface.blit(surf, rect)

			# enemies
			if tile.enemy:
				frames = self.animations[tile.enemy]['frames']
				index = int(self.animations[tile.enemy]['frame index'])
				surf = frames[index]
				rect = surf.get_rect(midbottom = (pos[0] + TILE_SIZE // 2, pos[1]+ TILE_SIZE))
				self.display_surface.blit(surf, rect)

			# items
			if tile.item:
				frames = self.animations[tile.item]['frames']
				index = int(self.animations[tile.item]['frame index'])
				surf = frames[index]
				if tile.item == 19:
					rect = surf.get_rect(midbottom = (pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE))
				else:
					rect = surf.get_rect(center = (pos[0] + TILE_SIZE // 2, pos[1]+ TILE_SIZE // 2))
				self.display_surface.blit(surf, rect)
    
		self.foreground.draw(self.display_surface)

	def preview(self):
		selected_object = self.mouse_on_object()
		if not self.menu.rect.collidepoint(mouse_pos()):
			if selected_object: # Drawing the highlight box around a hovered object
				rect = selected_object.rect.inflate(10,10)
				color = 'black'
				width = 3
				size = 15

				pygame.draw.lines(self.display_surface, color, False, ((rect.left,rect.top + size), rect.topleft, (rect.left + size,rect.top)), width)
				pygame.draw.lines(self.display_surface, color, False, ((rect.right - size,rect.top), rect.topright, (rect.right,rect.top + size)), width)
				pygame.draw.lines(self.display_surface, color, False, ((rect.right - size, rect.bottom), rect.bottomright, (rect.right,rect.bottom - size)), width)
				pygame.draw.lines(self.display_surface, color, False, ((rect.left,rect.bottom - size), rect.bottomleft, (rect.left + size,rect.bottom)), width)
				
			else: # Drawing the preview of the selected item
				type_dict = {key: value['type'] for key, value in EDITOR_DATA.items()}
				surf = self.preview_surfs[self.selection_index].copy()
				surf.set_alpha(200)
				
				if type_dict[self.selection_index] == 'tile':
					current_cell = self.get_current_cell()
					rect = surf.get_rect(center = self.origin + vector(current_cell) * TILE_SIZE + vector(TILE_SIZE // 2, TILE_SIZE // 2))
				else: # For objects
					rect = surf.get_rect(center = mouse_pos())
				self.display_surface.blit(surf, rect)

	def display_sky(self,dt):
		self.display_surface.fill(SKY_COLOR)
		y = self.sky_handle.rect.centery

		# horizon lines
		if y > 0:	
			horizon_rect1 = pygame.Rect(0,y - 10,WINDOW_WIDTH,10)
			horizon_rect2 = pygame.Rect(0,y - 16,WINDOW_WIDTH,4)
			horizon_rect3 = pygame.Rect(0,y - 20,WINDOW_WIDTH,2)
			pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect1)
			pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect2)
			pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect3)

			self.display_clouds(dt, y)

		# sea 
		if 0 < y < WINDOW_HEIGHT:
			sea_rect = pygame.Rect(0,y,WINDOW_WIDTH,WINDOW_HEIGHT)
			pygame.draw.rect(self.display_surface, SEA_COLOR, sea_rect)
			pygame.draw.line(self.display_surface, HORIZON_COLOR, (0,y), (WINDOW_WIDTH,y),3)
		if y < 0:
			self.display_surface.fill(SEA_COLOR)

	def display_clouds(self, dt, horizon_y):
		for cloud in self.current_clouds: # [{surf, pos, speed}]
			cloud['pos'][0] -= cloud['speed'] * dt
			x = cloud['pos'][0]
			y = horizon_y - cloud['pos'][1]
			self.display_surface.blit(cloud['surf'], (x,y))

	def create_clouds(self, event):
		if event.type == self.cloud_timer:
			surf = choice(self.cloud_surf)
			surf = pygame.transform.scale2x(surf) if randint(0,4) < 2 else surf
		
			pos = [WINDOW_WIDTH + randint(50,100),randint(0,WINDOW_HEIGHT)]
			self.current_clouds.append({'surf': surf, 'pos': pos, 'speed': randint(20,50)})

			# remove clouds
			self.current_clouds = [cloud for cloud in self.current_clouds if cloud['pos'][0] > -400]

	def startup_clouds(self):
		for i in range(20):
			surf = pygame.transform.scale2x(choice(self.cloud_surf)) if randint(0,4) < 2 else choice(self.cloud_surf)
			pos = [randint(0, WINDOW_WIDTH),randint(0, WINDOW_HEIGHT)]
			self.current_clouds.append({'surf': surf, 'pos': pos, 'speed': randint(20,50)})

	# update
	def run(self, dt):
		self.event_loop()

		# updating
		self.animation_update(dt)
		self.canvas_objects.update(dt)
		self.object_timer.update()

		# drawing
		self.display_surface.fill('gray')
		self.display_sky(dt)
		self.draw_level()
		self.draw_tile_lines()
		# pygame.draw.circle(self.display_surface, 'red', self.origin, 10)
		self.preview()
		self.menu.display(self.selection_index)

class CanvasTile:
	def __init__(self, tile_id, offset = vector()):

		# terrain
		self.has_terrain = False
		self.terrain_neighbors = []

		# water
		self.has_water = False
		self.water_on_top = False

		# coin
		self.coin = None

		# enemy
		self.enemy = None
  
		# item
		self.item = None

		# objects
		self.objects = []

		self.add_id(tile_id, offset = offset)
		self.is_empty = False

	def add_id(self, tile_id, offset = vector()):
		options = {key: value['style'] for key, value in EDITOR_DATA.items()}
		style = options.get(tile_id) # Use .get() for safety

		if style == 'terrain': self.has_terrain = True
		elif style == 'water': self.has_water = True
		elif style == 'coin': self.coin = tile_id
		elif style == 'enemy': self.enemy = tile_id
		# --- MODIFIED BLOCK ---
		elif style in ('chest', 'key', 'red_potion', 'blue_potion', 'map'): # <-- 'map' ĐƯỢC THÊM VÀO
			self.item = tile_id
		# --- END MODIFIED BLOCK ---
		elif style: 
			if (tile_id, offset) not in self.objects:
				self.objects.append((tile_id, offset))
		self.check_content() 

	def remove_id(self, tile_id):
		options = {key: value['style'] for key, value in EDITOR_DATA.items()}
		style = options.get(tile_id)

		if style == 'terrain': self.has_terrain = False
		elif style == 'water': self.has_water = False
		elif style == 'coin': self.coin = None
		elif style == 'enemy': self.enemy = None
		# --- MODIFIED BLOCK ---
		elif style in ('chest', 'key', 'red_potion', 'blue_potion', 'map'): 
			if self.item == tile_id:
				self.item = None
		# --- END MODIFIED BLOCK ---
		self.check_content()

	def check_content(self):
		if not self.has_terrain and not self.has_water and not self.coin and not self.enemy and not self.objects and not self.item:
			self.is_empty = True

	def get_water(self):
		return 'bottom' if self.water_on_top else 'top'

	def get_terrain(self):
		return ''.join(self.terrain_neighbors)

class CanvasObject(pygame.sprite.Sprite):
	def __init__(self, pos, frames, tile_id, origin, group, anchor='center'):
		super().__init__(group)
		self.tile_id = tile_id

		# animation
		self.frames = frames
		self.frame_index = 0

		self.image = self.frames[self.frame_index]
		self.rect = self.image.get_rect(**{anchor: pos})

		# movement
		self.distance_to_origin = vector(self.rect.topleft) - origin
		self.selected = False
		self.mouse_offset = vector()

	def start_drag(self):
		self.selected = True
		self.mouse_offset = vector(mouse_pos()) - vector(self.rect.topleft)

	def drag(self):
		if self.selected:
			self.rect.topleft = mouse_pos() - self.mouse_offset

	def drag_end(self, origin):
		self.selected = False
		self.distance_to_origin = vector(self.rect.topleft) - origin

	def animate(self, dt):
		self.frame_index += ANIMATION_SPEED * dt
		self.frame_index = 0 if self.frame_index >= len(self.frames) else self.frame_index
		self.image = self.frames[int(self.frame_index)]
		
		# Only update rect for animated objects if they aren't the player/sky handle
		if EDITOR_DATA[self.tile_id]['style'] not in ('player', 'sky'):
			pass

	def pan_pos(self, origin):
		self.rect.topleft = origin + self.distance_to_origin

	def update(self, dt):
		self.animate(dt)
		self.drag()