import pygame, sys, os
from pygame.math import Vector2 as vector

from settings import *
from support import *

from sprites import Generic, Block, Animated, Particle, Coin, Player, Spikes, Tooth, Shell, Cloud, Item, Chest, Pearl, Crabby 
from inventory import Inventory
from option_menu import OptionMenu

from random import choice, randint

class Level:
	def __init__(self, grid, switch, asset_dict, audio):
		self.display_surface = pygame.display.get_surface()
		self.switch = switch

		if grid.get('terrain'):
			terrain_keys = grid['terrain'].keys()
			self.level_limits = {
				'left': min(terrain_keys, key=lambda pos: pos[0])[0],
				'right': max(terrain_keys, key=lambda pos: pos[0])[0] + TILE_SIZE
			}
		else:
			self.level_limits = {'left': 0, 'right': WINDOW_WIDTH}

		# Sprite groups setup...
		self.all_sprites = CameraGroup(self.level_limits)
		self.coin_sprites = pygame.sprite.Group()
		self.damage_sprites = pygame.sprite.Group()
		self.collision_sprites = pygame.sprite.Group() 
		self.shell_sprites = pygame.sprite.Group()
		self.attackable_sprites = pygame.sprite.Group() 
		self.item_sprites = pygame.sprite.Group() 
		self.boss_sprites = pygame.sprite.Group()       

		# Chest
		self.pending_chests = []
		self.boss_defeated = False

		# Boundary walls setup
		wall_height = self.level_limits['right'] * 2
		Block((self.level_limits['left'] - 5, -wall_height / 2), (5, wall_height), self.collision_sprites)
		Block((self.level_limits['right'], -wall_height / 2), (5, wall_height), self.collision_sprites)

		# Checkpoint setup
		self.player_start_pos = vector()
		self.last_checkpoint = None

		# Build the level
		self.build_level(grid, asset_dict, audio['jump'], audio['hit']) 

		# Assets and UI setup.
		self.particle_surfs = asset_dict['particle']
		self.cloud_surfs = asset_dict['clouds']
		self.player_health_bar = asset_dict['player_health_bar']
		self.inventory = Inventory(self.player, asset_dict['inventory']) 
		self.item_effects = asset_dict['item_effects']
  
		# HUD assets
		self.hud_assets = asset_dict['hud_assets']
		try:
			self.hud_font = pygame.font.Font(FONT, 24)
		except Exception:
			self.hud_font = pygame.font.Font(None, 28)

		# Cloud timer setup
		self.cloud_timer = pygame.USEREVENT + 2
		pygame.time.set_timer(self.cloud_timer, 2000)
		self.startup_clouds()

		# Sounds setup
		self.bg_music = audio['music']
		self.coin_sound = audio['coin']
		self.hit_sound = audio['hit']
		self.chest_locked_sound = audio['chest_locked']
		self.chest_open_sound = audio['chest_open']

		# Option menu setup
		self.option_menu = OptionMenu(
			state_switch_callback=self.switch,
			music_track=self.bg_music,
			sfx_sounds=audio
		)
		self.option_menu.from_menu = False
 
	def build_level(self, grid, asset_dict, jump_sound, hit_sound):
		# Create Player first
		player_pos = (0,0) # default
		for layer_name, layer in grid.items():
			for pos, data in layer.items():
				if data == 0: player_pos = pos; break
		self.player_start_pos = vector(player_pos)
		self.player = Player(player_pos, asset_dict['player'], self.all_sprites, self.collision_sprites, jump_sound)

		# Build everything else
		for layer_name, layer in grid.items():
			for pos, data in layer.items():
				if layer_name == 'terrain':
					Generic(pos, asset_dict['land'][data], [self.all_sprites, self.collision_sprites])
				if layer_name == 'water':
					if data == 'top': Animated(asset_dict['water top'], pos, self.all_sprites, LEVEL_LAYERS['water'])
					else: Generic(pos, asset_dict['water bottom'], self.all_sprites, LEVEL_LAYERS['water'])

				match data:
					# case 0 handled above
					case 1: self.horizon_y = pos[1]; self.all_sprites.horizon_y = pos[1]
					case 4: Coin('gold', asset_dict['gold'], pos, [self.all_sprites, self.coin_sprites])
					case 5: Coin('silver', asset_dict['silver'], pos, [self.all_sprites, self.coin_sprites])
					case 6: Coin('diamond', asset_dict['diamond'], pos, [self.all_sprites, self.coin_sprites])
					case 7: Spikes(asset_dict['spikes'], pos, [self.all_sprites, self.damage_sprites])
					case 8: Tooth(asset_dict['tooth'], pos, [self.all_sprites, self.attackable_sprites], self.collision_sprites, asset_dict['small_health_bar'])
					case 9: Shell('left', asset_dict['shell'], pos, [self.all_sprites, self.collision_sprites, self.shell_sprites, self.attackable_sprites], asset_dict['pearl'], asset_dict['pearl_destroyed'], self.damage_sprites, asset_dict['small_health_bar'], self.attackable_sprites, self.collision_sprites)
					case 10: Shell('right', asset_dict['shell'], pos, [self.all_sprites, self.collision_sprites, self.shell_sprites, self.attackable_sprites], asset_dict['pearl'], asset_dict['pearl_destroyed'], self.damage_sprites, asset_dict['small_health_bar'], self.attackable_sprites, self.collision_sprites)
					case 11: Animated(asset_dict['palms']['small_fg'], pos, self.all_sprites); Block(pos, (76,50), self.collision_sprites)
					case 12: Animated(asset_dict['palms']['large_fg'], pos, self.all_sprites); Block(pos, (76,50), self.collision_sprites)
					case 13: Animated(asset_dict['palms']['left_fg'], pos, self.all_sprites); Block(pos, (76,50), self.collision_sprites)
					case 14: Animated(asset_dict['palms']['right_fg'], pos, self.all_sprites); Block(pos + vector(50,0), (76,50), self.collision_sprites)
					case 15: Animated(asset_dict['palms']['small_bg'], pos, self.all_sprites, LEVEL_LAYERS['bg'])
					case 16: Animated(asset_dict['palms']['large_bg'], pos, self.all_sprites, LEVEL_LAYERS['bg'])
					case 17: Animated(asset_dict['palms']['left_bg'], pos, self.all_sprites, LEVEL_LAYERS['bg'])
					case 18: Animated(asset_dict['palms']['right_bg'], pos, self.all_sprites, LEVEL_LAYERS['bg'])
					case 19: self.pending_chests.append({'pos': pos, 'assets': asset_dict['chest']}) # Chest(asset_dict['chest'], pos, [self.all_sprites, self.collision_sprites, self.item_sprites])
					case 20: Item('key', asset_dict['items']['key'], pos, [self.all_sprites, self.collision_sprites, self.item_sprites])
					case 21: Item('red_potion', asset_dict['items']['red_potion'], pos, [self.all_sprites, self.collision_sprites, self.item_sprites])
					case 22: Item('blue_potion', asset_dict['items']['blue_potion'], pos, [self.all_sprites, self.collision_sprites, self.item_sprites])
					case 23:
						midbottom_pos = (pos[0] + TILE_SIZE//2, pos[1] + TILE_SIZE)
						Crabby(asset_dict['crabby'], midbottom_pos, [self.all_sprites, self.attackable_sprites, self.boss_sprites, self.damage_sprites], self.collision_sprites, self.item_sprites, self.attackable_sprites, asset_dict['boss_health_bar'], self.player, None, 'midbottom')
					case 24: Item('map', asset_dict['items']['map'], pos, [self.all_sprites, self.collision_sprites, self.item_sprites])

		for sprite in self.shell_sprites: sprite.player = self.player
		for sprite in self.attackable_sprites:
			if isinstance(sprite, Tooth): sprite.player = self.player

	def get_coins(self):
		collided_coins = pygame.sprite.spritecollide(self.player, self.coin_sprites, True)
		for sprite in collided_coins:
			self.coin_sound.play()
			Particle(self.particle_surfs, sprite.rect.center, self.all_sprites)
   
			if sprite.coin_type in self.player.coin_counts:
				self.player.coin_counts[sprite.coin_type] += 1

	def get_damage(self):
		collision_sprites = pygame.sprite.spritecollide(self.player, self.damage_sprites, False, pygame.sprite.collide_mask)

		if collision_sprites and not self.player.invul_timer.active:
			sprite = collision_sprites[0] 

			if isinstance(sprite, Pearl):
				self.hit_sound.play()
				self.player.damage(1)
			elif isinstance(sprite, Spikes): 
				self.hit_sound.play()
				self.player.damage(1)

	def draw_player_health_bar(self):
		bar_surf = self.player_health_bar['bar']
		red_surf = self.player_health_bar['red']
		bar_pos = (20, 10)
		bar_rect = bar_surf.get_rect(topleft=bar_pos)
		health_ratio = max(0, self.player.health / self.player.max_health)
		red_width = red_surf.get_width() * health_ratio
		red_crop_rect = pygame.Rect(0, 0, red_width, red_surf.get_height())
		red_pos = (bar_rect.left + 34, bar_rect.centery - red_surf.get_height() / 2 - 2)
		self.display_surface.blit(bar_surf, bar_pos)
		self.display_surface.blit(red_surf, red_pos, red_crop_rect)

	def draw_hud_text(self, surface, text, pos, font, color=(255, 255, 255), stroke_color='#3e3546'):
		# Stroke
		stroke_offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
		for offset in stroke_offsets:
			stroke_surf = font.render(text, True, stroke_color)
			stroke_rect = stroke_surf.get_rect(midleft=pos)
			stroke_rect.move_ip(offset)
			surface.blit(stroke_surf, stroke_rect)

		# Main text
		text_surf = font.render(text, True, color)
		text_rect = text_surf.get_rect(midleft=pos)
		surface.blit(text_surf, text_rect)
  
	def draw_coin_hud(self):
		# Position below health bar
		start_x = 20
		start_y = 60 # Health bar is at (20, 10)
		text_offset = vector(5, 0)
		icon_spacing = 90 # Space between start of icons

		# Silver 
		silver_img = self.hud_assets['silver']
		silver_rect = silver_img.get_rect(topleft=(start_x, start_y))
		self.display_surface.blit(silver_img, silver_rect)
		self.draw_hud_text(
			self.display_surface,
			f"x{self.player.coin_counts['silver']}",
			silver_rect.midright + text_offset,
			self.hud_font
		)

		# Gold
		gold_img = self.hud_assets['gold']
		gold_rect = gold_img.get_rect(topleft=(silver_rect.left + icon_spacing, start_y))
		self.display_surface.blit(gold_img, gold_rect)
		self.draw_hud_text(
			self.display_surface,
			f"x{self.player.coin_counts['gold']}",
			gold_rect.midright + text_offset,
			self.hud_font
		)

		# Diamond
		diamond_img = self.hud_assets['diamond']
		diamond_rect = diamond_img.get_rect(topleft=(gold_rect.left + icon_spacing, start_y))
		self.display_surface.blit(diamond_img, diamond_rect)
		self.draw_hud_text(
			self.display_surface,
			f"x{self.player.coin_counts['diamond']}",
			diamond_rect.midright + text_offset,
			self.hud_font
		)

	def player_attack(self):
		if self.player.attack_timer.active:
			damage = 2 if self.player.status == 'air-attack' else 1
			attack_offset = vector(40, 0) if self.player.orientation == 'right' else vector(-40, 0)
			attack_rect = pygame.Rect(self.player.rect.center + attack_offset, (60, self.player.rect.height))
			for enemy in self.attackable_sprites:
				if enemy.rect.colliderect(attack_rect):
					enemy.damage(damage)

	def tooth_attack_damage(self):
		for sprite in self.attackable_sprites:
			if isinstance(sprite, Tooth) and sprite.status == 'attack' and sprite.is_alive:
				if sprite.attack_rect.colliderect(self.player.hitbox) and not self.player.invul_timer.active:
					self.hit_sound.play()
					self.player.damage(2)

	def save_checkpoint(self, pos):
		self.last_checkpoint = vector(pos)

	def respawn_player(self):
		respawn_pos_center = vector()
		if self.last_checkpoint:
			respawn_pos_center = vector(self.last_checkpoint.x, self.last_checkpoint.y - self.player.rect.height / 2)
		else:
			respawn_pos_center = self.player_start_pos + vector(self.player.rect.width / 2, self.player.rect.height / 2)

		self.player.pos = respawn_pos_center
		self.player.rect.center = round(self.player.pos.x), round(self.player.pos.y) # Round for pixel coords
		self.player.hitbox.center = self.player.rect.center

		self.player.health = self.player.max_health
		self.player.direction = vector(0,0) # Reset ALL momentum
		self.player.invul_timer.activate()

	def check_interaction(self):
		interaction_rect = self.player.hitbox.inflate(20, 20)
		for sprite in self.item_sprites:
			if interaction_rect.colliderect(sprite.rect):
				if isinstance(sprite, Chest):
					if 'key' in self.player.inventory:
						self.chest_open_sound.play()
						sprite.interact()
						del self.player.inventory['key']
						self.player.inventory = {k: v for k, v in self.player.inventory.items()}
      
						self.switch(action='end_game')
						return True
					else:
						self.chest_locked_sound.play()
					return True
				elif isinstance(sprite, Item):
					item_style = sprite.item_style
					if item_style == 'map':
						self.save_checkpoint(sprite.rect.midbottom)
						self.coin_sound.play()
						effect_surf = self.item_effects['key']
						Particle(effect_surf, sprite.rect.center, self.all_sprites)
						sprite.kill()
						return True
					if len(self.player.inventory) < 3 or item_style in self.player.inventory:
						if item_style == 'key':
							if 'key' not in self.player.inventory: self.player.inventory['key'] = 1
							else: continue
						else:
							self.player.inventory[item_style] = self.player.inventory.get(item_style, 0) + 1
						self.coin_sound.play()
						effect_surf = self.item_effects.get(item_style, self.item_effects.get('potion')) 
						if effect_surf: 
							Particle(effect_surf, sprite.rect.center, self.all_sprites)
						sprite.kill()
						return True
		return False

	def check_boss_defeat(self):
		if not self.boss_defeated:
			living_bosses = [boss for boss in self.boss_sprites if boss.is_alive]
			if not living_bosses and self.boss_sprites:
				self.boss_defeated = True
				self.spawn_chests()
    
	def spawn_chests(self):
		print("Boss defeated! Spawning chest(s)...") # Debug message
		for chest_data in self.pending_chests:
			Chest(
				assets=chest_data['assets'],
				pos=chest_data['pos'],
				group=[self.all_sprites, self.collision_sprites, self.item_sprites]
			)
		self.pending_chests = []
	
	def startup_clouds(self):
		# Safety check for horizon_y
		if not hasattr(self, 'horizon_y'):
			self.horizon_y = WINDOW_HEIGHT / 2
		for i in range(40):
			surf = choice(self.cloud_surfs)
			surf = pygame.transform.scale2x(surf) if randint(0,5) > 3 else surf
			x = randint(self.level_limits['left'], self.level_limits['right'])
			y = self.horizon_y - randint(-50,600)
			Cloud((x,y), surf, self.all_sprites, self.level_limits['left'])

	def run(self, dt):
		events = pygame.event.get()
		menu_action = self.option_menu.handle_events(events)
		if menu_action == 'menu': return

		for event in events:
			if event.type == pygame.QUIT: pygame.quit(); sys.exit()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE: self.switch(action='menu'); return
			if not self.option_menu.active:
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_z: self.inventory.toggle()
					if event.key == pygame.K_f:
						if not self.check_interaction(): self.player.start_attack()
			if event.type == self.cloud_timer:
				surf = choice(self.cloud_surfs)
				surf = pygame.transform.scale2x(surf) if randint(0,5) > 3 else surf
				x = self.level_limits['right'] + randint(100,300)
				y = self.horizon_y - randint(-50,600)
				Cloud((x,y), surf, self.all_sprites, self.level_limits['left'])

		if self.option_menu.active:
			self.display_surface.fill(SKY_COLOR)
			self.all_sprites.custom_draw(self.player)
			self.draw_player_health_bar()
			self.draw_coin_hud()
			self.inventory.display()
			self.option_menu.draw()
			return

		if not self.inventory.visible:
			self.all_sprites.update(dt)
			self.player_attack()
		else:
			self.inventory.update()
			for sprite in self.all_sprites:
				if not isinstance(sprite, Player): sprite.update(dt)

		self.check_boss_defeat()
  
		self.get_coins()
		self.get_damage()
		self.tooth_attack_damage()

		if self.player.health <= 0:
			self.respawn_player()

		self.display_surface.fill(SKY_COLOR)
		self.all_sprites.custom_draw(self.player)
		self.draw_player_health_bar()
		self.draw_coin_hud()
		self.inventory.display()
		self.option_menu.draw()

class CameraGroup(pygame.sprite.Group):
	def __init__(self, level_limits):
		super().__init__()
		self.display_surface = pygame.display.get_surface()
		self.offset = vector()
		self.level_limits = level_limits
		self.camera_rect = pygame.Rect(WINDOW_WIDTH / 4, WINDOW_HEIGHT / 4, WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
		self.horizon_y = WINDOW_HEIGHT / 2 + 100 

	def draw_horizon(self):
		horizon_pos = self.horizon_y - self.offset.y

		if horizon_pos < WINDOW_HEIGHT:
			sea_rect = pygame.Rect(0,horizon_pos,WINDOW_WIDTH,WINDOW_HEIGHT - horizon_pos)
			pygame.draw.rect(self.display_surface, SEA_COLOR, sea_rect)

			h_rect1 = pygame.Rect(0,horizon_pos - 10,WINDOW_WIDTH,10)
			h_rect2 = pygame.Rect(0,horizon_pos - 16,WINDOW_WIDTH,4)
			h_rect3 = pygame.Rect(0,horizon_pos - 20,WINDOW_WIDTH,2)
			pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, h_rect1)
			pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, h_rect2)
			pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, h_rect3)
			pygame.draw.line(self.display_surface, HORIZON_COLOR, (0,horizon_pos), (WINDOW_WIDTH,horizon_pos), 3)

		if horizon_pos < 0:
			self.display_surface.fill(SEA_COLOR)

	def custom_draw(self, player):
		if player.rect.left < self.camera_rect.left: self.camera_rect.left = player.rect.left
		if player.rect.right > self.camera_rect.right: self.camera_rect.right = player.rect.right
		if player.rect.top < self.camera_rect.top: self.camera_rect.top = player.rect.top
		if player.rect.bottom > self.camera_rect.bottom: self.camera_rect.bottom = player.rect.bottom

		self.offset = vector(
			self.camera_rect.centerx - WINDOW_WIDTH / 2,
			self.camera_rect.centery - WINDOW_HEIGHT / 2)

		# Camera limits... (same as before)
		if self.offset.x < self.level_limits['left']: self.offset.x = self.level_limits['left']
		if self.offset.x > self.level_limits['right'] - WINDOW_WIDTH: self.offset.x = self.level_limits['right'] - WINDOW_WIDTH

		# Draw clouds (no parallax)
		for sprite in self:
			if sprite.z == LEVEL_LAYERS['clouds']:
				offset_rect = sprite.rect.copy()
				offset_rect.center -= self.offset
				self.display_surface.blit(sprite.image, offset_rect)

		# Draw horizon
		self.draw_horizon()

		# Draw everything else by layer order
		for layer in LEVEL_LAYERS.values():
			for sprite in self:
				if sprite.z == layer and sprite.z != LEVEL_LAYERS['clouds']:
					offset_rect = sprite.rect.copy()
					offset_rect.center -= self.offset
					self.display_surface.blit(sprite.image, offset_rect)

					# Draw health bars on top of enemies (will be drawn when processing 'main' layer)
					if hasattr(sprite, 'health') and not isinstance(sprite, Player):
						if hasattr(sprite, 'draw_small_health_bar'):
							sprite.draw_small_health_bar(self.display_surface, self.offset)
						elif hasattr(sprite, 'draw_boss_health_bar'):
							sprite.draw_boss_health_bar(self.display_surface, self.offset)