import pygame, sys, os, json
from pygame.math import Vector2 as vector

from settings import *
from support import *

from pygame.image import load

from menu import MainMenu
from end_menu import EndMenu
from editor import Editor
from level import Level

from os import walk

class Main:
	def __init__(self):
		pygame.init()
		self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
		self.clock = pygame.time.Clock()
		self.imports()

		self.menu_active = True
		self.editor_active = False 
		self.level_active = False
		self.level = None 
		
		self.level_grid = self.load_level_grid() 

		self.music_channel = pygame.mixer.find_channel()
		
		self.menu = MainMenu(self.menu_music, self.level_sounds) 
		self.end_menu_active = False
		self.end_menu = None
		
		self.music_channel.play(self.menu_music, loops=-1) 
		
		self.editor = Editor(self.land_tiles, self.switch, self.level_grid)
		self.editor.editor_music.stop() 

		surf = load('assets/graphics/cursors/mouse.png').convert_alpha()
		cursor = pygame.cursors.Cursor((0,0), surf)
		pygame.mouse.set_cursor(cursor)

	def imports(self):
		# terrain
		self.land_tiles = import_folder_dict('assets/graphics/terrain/land')
		self.water_bottom = load('assets/graphics/terrain/water/water_bottom.png').convert_alpha()
		self.water_top_animation = import_folder('assets/graphics/terrain/water/animation')

		# coins
		self.gold = import_folder('assets/graphics/items/gold')
		self.silver = import_folder('assets/graphics/items/silver')
		self.diamond = import_folder('assets/graphics/items/diamond')
		self.particle = import_folder('assets/graphics/items/particle')

		# palm trees
		self.palms = {folder: import_folder(f'assets/graphics/terrain/palm/{folder}') for folder in list(walk('assets/graphics/terrain/palm'))[0][1]}

		# enemies
		self.spikes = load('assets/graphics/enemies/spikes/spikes.png').convert_alpha()
		self.tooth = {folder: import_folder(f'assets/graphics/enemies/tooth/{folder}') for folder in list(walk('assets/graphics/enemies/tooth'))[0][1]}
		self.shell = {folder: import_folder(f'assets/graphics/enemies/shell_left/{folder}') for folder in list(walk('assets/graphics/enemies/shell_left/'))[0][1]}
		self.pearl_surf = load('assets/graphics/enemies/pearl/pearl.png').convert_alpha()
		self.pearl_destroyed = import_folder('assets/graphics/enemies/pearl/destroyed')
		self.crabby = {folder: import_folder(f'assets/graphics/enemies/crabby/{folder}') for folder in list(walk('assets/graphics/enemies/crabby'))[0][1]}

		# player
		self.player_graphics = {folder: import_folder(f'assets/graphics/player/{folder}') for folder in list(walk('assets/graphics/player/'))[0][1]}

		# clouds
		self.clouds = import_folder('assets/graphics/clouds')

		# health bars
		self.small_health_bar = {
			'bar': load('assets/graphics/items/small bars/bar.png').convert_alpha(),
			'red': load('assets/graphics/items/small bars/red.png').convert_alpha()
		}
		self.player_health_bar = {
			'bar': load('assets/graphics/items/life bars/player.png').convert_alpha(),
			'red': load('assets/graphics/items/life bars/red.png').convert_alpha()
		}
		self.boss_health_bar = {
			'bar': load('assets/graphics/items/life bars/enemy.png').convert_alpha(),
			'red': load('assets/graphics/items/life bars/red.png').convert_alpha()
		}
  
		# items
		self.item_assets = {
			'key': import_folder('assets/graphics/items/key/idle'),
			'red_potion': import_folder('assets/graphics/items/potion/red'),
			'blue_potion': import_folder('assets/graphics/items/potion/blue'),
			'map': import_folder('assets/graphics/items/map/idle'), 
		}
  
		self.chest_assets = {
			'idle': import_folder('assets/graphics/items/chest/idle'),
			'unlocked': import_folder('assets/graphics/items/chest/unlocked')
		}
  
		self.item_effects = {
			'key': import_folder('assets/graphics/items/key/effect'),
			'potion': import_folder('assets/graphics/items/potion/effect')
		}
		
		# inventory
		self.inventory_assets = {
			'cell': load('assets/graphics/inventory/cell.png').convert_alpha(),
			'items': {
				'key': load('assets/graphics/inventory/key.png').convert_alpha(),
				'red_potion': load('assets/graphics/inventory/red_potion.png').convert_alpha(),
				'blue_potion': load('assets/graphics/inventory/blue_potion.png').convert_alpha(),
			}
		}
  
		# hud
		self.hud_assets = {
			'gold': load('assets/graphics/end-menu/gold.png').convert_alpha(),
			'silver': load('assets/graphics/end-menu/silver.png').convert_alpha(),
			'diamond': load('assets/graphics/end-menu/diamond.png').convert_alpha()
		}
  
		# sounds
		self.menu_music = pygame.mixer.Sound('assets/audio/SuperHero.ogg')
  
		self.level_sounds = {
			'coin': pygame.mixer.Sound('assets/audio/coin.wav'),
			'hit': pygame.mixer.Sound('assets/audio/hit.wav'),
			'jump': pygame.mixer.Sound('assets/audio/jump.wav'),
			'music': pygame.mixer.Sound('assets/audio/SuperHero.ogg'), 
			'chest_locked': pygame.mixer.Sound('assets/audio/wooden-thud-mono.mp3'),
			'chest_open': pygame.mixer.Sound('assets/audio/chest-opening.mp3'),
		}
  
		self.level_sounds['music'] = self.menu_music

	def load_level_grid(self):
		filename = "saved_level_grid.json"
		load_path = os.path.join("data", filename)
		
		if not os.path.exists(load_path):
			return None

		try:
			with open(load_path, "r") as f:
				serializable_grid = json.load(f)
			
			loaded_grid = {}
			for layer_name, layer_data in serializable_grid.items():
				loaded_grid[layer_name] = {tuple(map(int, k.split(','))): v for k, v in layer_data.items()}
				
			print(f"Loaded existing level data from {load_path}.")
			return loaded_grid

		except Exception as e:
			print(f"Error loading level data: {e}")
			return None

	def switch(self, grid = None, action = None):
		if action == 'menu':
			self.menu_active = True
			self.editor_active = False
			self.level_active = False
			self.end_menu_active = False
			self.end_menu = None
			self.editor.editor_music.stop() 
			if self.level:
				self.level = None
			
			self.music_channel.play(self.menu_music, loops=-1)

			if grid:
				self.level_grid = grid 
		
		elif action == 'new_game' or grid:
			if not self.level_grid:
				print("Cannot start game: self.level_grid is empty.")
				return
				
			self.menu_active = False
			self.editor_active = False
			self.level_active = True
			self.end_menu_active = False
			self.end_menu = None
   
			self.level = Level(
				self.level_grid, 
				self.switch, 
				{
					'land': self.land_tiles,
					'water bottom': self.water_bottom,
					'water top': self.water_top_animation,
					'gold': self.gold,
					'silver': self.silver,
					'diamond': self.diamond,
					'particle': self.particle,
					'palms': self.palms,
					'spikes': self.spikes,
					'tooth': self.tooth,
					'shell': self.shell,
					'player': self.player_graphics,
					'pearl': self.pearl_surf,
					'pearl_destroyed': self.pearl_destroyed,
					'clouds': self.clouds,
					'small_health_bar': self.small_health_bar,
					'player_health_bar': self.player_health_bar,
					'boss_health_bar': self.boss_health_bar,
					'items': self.item_assets,
					'chest': self.chest_assets, 
					'item_effects': self.item_effects,
					'inventory': self.inventory_assets,
					'crabby': self.crabby, 
					'hud_assets': self.hud_assets,
				},
				self.level_sounds 
			)
		
		elif action == 'editor':
			self.menu_active = False
			self.level_active = False
			self.editor_active = True
			self.music_channel.stop() 
			self.editor.editor_music.play(loops = -1)
   
		elif action == 'end_game':
			background_level_capture = None
			if self.level: # Get coin data from the level
				coin_counts = self.level.player.coin_counts
				background_level_capture = self.level
				self.level = None # Clear the level
			else:
				coin_counts = {} # Fallback
			
			self.menu_active = False
			self.editor_active = False
			self.level_active = False
			self.end_menu_active = True
			self.end_menu = EndMenu(coin_counts, self.switch, background_level_capture)
			
	def run(self):
		while True:
			dt = self.clock.tick(60) / 1000
			dt = min(dt, 1 / 30)
			
			if self.menu_active:
				action = self.menu.run()
				
				if action == "editor":
					self.switch(action='editor') 
				
				elif action == "new_game":
					if self.level_grid:
						self.switch(action='new_game') 
					else:
						print("No saved level found. Please enter the editor first and press ENTER to create/save a level.")
				
				elif action == "quit":
					pygame.quit()
					sys.exit()

			elif self.editor_active:
				self.editor.run(dt)
			
			elif self.level_active and self.level:
				self.level.run(dt)
    
			elif self.end_menu_active and self.end_menu:
				action = self.end_menu.run()
				if action == 'menu':
					self.switch(action='menu')
				
			pygame.display.update()

if __name__ == '__main__':
	main = Main()
	main.run()