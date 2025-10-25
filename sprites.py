# sprites.py
import pygame
from pygame.math import Vector2 as vector
from settings import *
from timer import Timer
from random import choice, randint

class Generic(pygame.sprite.Sprite):
	def __init__(self, pos, surf, group, z = LEVEL_LAYERS['main']):
		super().__init__(group)
		self.image = surf
		self.rect = self.image.get_rect(topleft = pos)
		self.z = z

class Block(Generic):
	def __init__(self, pos, size, group):
		surf = pygame.Surface(size)
		super().__init__(pos, surf, group)

class Cloud(Generic):
	def __init__(self, pos, surf, group, left_limit):
		super().__init__(pos, surf, group, LEVEL_LAYERS['clouds'])
		self.left_limit = left_limit
		self.pos = vector(self.rect.topleft)
		self.speed = randint(20,30)

	def update(self, dt):
		self.pos.x -= self.speed * dt
		self.rect.x = round(self.pos.x)
		if self.rect.x <= self.left_limit:
			self.kill()

class Animated(Generic):
	def __init__(self, assets, pos, group, z = LEVEL_LAYERS['main']):
		self.animation_frames = assets
		self.frame_index = 0
		if not assets: # Handle empty asset list
			print(f"Warning: Empty asset list passed to Animated at {pos}")
			# Create a fallback surface or handle appropriately
			self.animation_frames = [pygame.Surface((TILE_SIZE,TILE_SIZE))]
			self.animation_frames[0].fill('magenta') # Magenta usually indicates an error
		super().__init__(pos, self.animation_frames[self.frame_index], group, z)


	def animate(self, dt):
		if not self.animation_frames: return # Safety check
		self.frame_index += ANIMATION_SPEED * dt
		self.frame_index %= len(self.animation_frames) # Use modulo for looping
		self.image = self.animation_frames[int(self.frame_index)]

	def update(self, dt):
		self.animate(dt)

class Particle(Animated):
	def __init__(self, assets, pos, group):
		super().__init__(assets, pos, group)
		self.rect = self.image.get_rect(center = pos)

	def animate(self, dt):
		if not self.animation_frames: self.kill(); return # Safety check
		self.frame_index += ANIMATION_SPEED * dt
		if self.frame_index < len(self.animation_frames):
			self.image = self.animation_frames[int(self.frame_index)]
		else:
			self.kill()

class Coin(Animated):
	def __init__(self, coin_type, assets, pos, group):
		super().__init__(assets, pos, group)
		self.rect = self.image.get_rect(center = pos)
		self.coin_type = coin_type

class Item(Animated):
	def __init__(self, item_style, assets, pos, group):
		super().__init__(assets, pos, group)
		self.rect = self.image.get_rect(topleft = pos)
		self.item_style = item_style

class Chest(Generic):
	def __init__(self, assets, pos, group):
		self.animation_frames = assets
		self.frame_index = 0
		self.status = 'idle'
		if 'idle' not in self.animation_frames or not self.animation_frames['idle']:
			print(f"ERROR: Chest 'idle' animation missing or empty!")
			fallback_surf = pygame.Surface((TILE_SIZE, TILE_SIZE)); fallback_surf.fill('purple')
			if 'idle' not in self.animation_frames: self.animation_frames['idle'] = []
			self.animation_frames['idle'].append(fallback_surf)
		if 'unlocked' not in self.animation_frames: self.animation_frames['unlocked'] = self.animation_frames['idle']

		super().__init__(pos, self.animation_frames[self.status][self.frame_index], group)
		self.rect.midbottom = (pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE)

	def interact(self):
		if self.status == 'idle':
			self.status = 'unlocked'; self.frame_index = 0

	def animate(self, dt):
		current_animation = self.animation_frames[self.status]
		if not current_animation: return

		self.frame_index += ANIMATION_SPEED * dt
		if self.frame_index >= len(current_animation):
			if self.status == 'unlocked': self.kill()
			else: self.frame_index = 0
		if int(self.frame_index) < len(current_animation):
			self.image = current_animation[int(self.frame_index)]

	def update(self, dt):
		self.animate(dt)

class Spikes(Generic):
	def __init__(self, surf, pos, group):
		super().__init__(pos, surf, group)
		self.mask = pygame.mask.from_surface(self.image)

class Tooth(Generic):
	def __init__(self, assets, pos, group, collision_sprites, health_bar_assets):
		self.animation_frames = assets
		self.frame_index = 0
		self.status = 'run'
		self.orientation = choice(['left', 'right']) 
		init_key = f'{self.status}_{self.orientation}'
		if init_key not in self.animation_frames:
			opposite_orientation = 'left' if self.orientation == 'right' else 'right'
			fallback_key = f'{self.status}_{opposite_orientation}'
			if fallback_key in self.animation_frames:
				self.orientation = opposite_orientation
				init_key = fallback_key
			elif 'run_right' in self.animation_frames:
				init_key = 'run_right'
				self.orientation = 'right'
			else:
				if self.animation_frames:
					init_key = list(self.animation_frames.keys())[0]
					self.status, self.orientation = init_key.split('_')
				else: 
					print("ERROR: Tooth animations completely missing!")
					dummy_surf = pygame.Surface((TILE_SIZE // 2, TILE_SIZE // 2)); dummy_surf.fill('red')
					self.animation_frames[init_key] = [dummy_surf]

		surf = self.animation_frames[init_key][self.frame_index]
		super().__init__(pos, surf, group)
		self.rect.bottom = self.rect.top + TILE_SIZE 
		self.mask = pygame.mask.from_surface(self.image)
		self.pos = vector(self.rect.topleft)

		# Movement
		self.direction = vector(1, 0) if self.orientation == 'right' else vector(-1, 0)
		self.speed = 120
		self.collision_sprites = collision_sprites

		# Patrol Area
		self.patrol_center_x = self.rect.centerx
		self.patrol_radius = TILE_SIZE * 3

		# Health and damage
		self.health = 10
		self.hit_timer = Timer(250)
		self.bar_surf = health_bar_assets['bar']
		self.red_surf = health_bar_assets['red']
		self.is_alive = True

		# AI and interaction
		self.player = None
		self.is_alerted = False
		self.detection_radius = 250
		self.chase_radius = 400
		self.attack_rect = pygame.Rect(0, 0, 40, self.rect.height)

		# Kill if spawned mid-air
		if not any(sprite.rect.collidepoint(self.rect.midbottom + vector(0, 5)) for sprite in collision_sprites):
			print(f"Tooth killed: Spawned mid-air at {pos}")
			self.kill()

	def get_status(self):
		if self.hit_timer.active or not self.is_alive: return

		if self.player:
			distance = vector(self.rect.center).distance_to(self.player.rect.center)
			# Update alert status based on distance
			self.is_alerted = distance < self.chase_radius if self.is_alerted else distance < self.detection_radius

		# Set status based on alert state
		self.status = 'attack' if self.is_alerted else 'run'

	def animate(self, dt):
		animation_key = f'{self.status}_{self.orientation}'
		if not self.is_alive: animation_key = f'dead-hit_{self.orientation}'
		elif self.hit_timer.active: animation_key = f'hit_{self.orientation}'

		if animation_key not in self.animation_frames:
			fallback_key = f'run_{self.orientation}'
			if fallback_key in self.animation_frames: animation_key = fallback_key
			else: print(f"ERROR: Missing animation '{animation_key}' for Tooth!"); return

		current_animation = self.animation_frames[animation_key]
		self.frame_index += ANIMATION_SPEED * dt

		if self.frame_index >= len(current_animation):
			if not self.is_alive:
				self.frame_index = len(current_animation) - 1
				new_alpha = max(0, self.image.get_alpha() - 10); self.image.set_alpha(new_alpha)
				if new_alpha == 0: self.kill()
			else: self.frame_index = 0

		if self.alive() and int(self.frame_index) < len(current_animation):
			self.image = current_animation[int(self.frame_index)]
			self.mask = pygame.mask.from_surface(self.image)

	def update_attack_rect(self):
		if self.orientation == 'right': self.attack_rect.midleft = self.rect.midright
		else: self.attack_rect.midright = self.rect.midleft

	def move(self, dt):
		if self.hit_timer.active or not self.is_alive: return

		target_direction_x = self.direction.x 
  
		if self.is_alerted and self.player:
			# Chase Player
			player_direction_x = self.player.rect.centerx - self.rect.centerx
			# Stop slightly away from player to attack
			attack_distance_threshold = TILE_SIZE * 0.6
			if abs(player_direction_x) < attack_distance_threshold: target_direction_x = 0
			else: target_direction_x = 1 if player_direction_x > 0 else -1
			# Update orientation based on target direction
			if target_direction_x != 0: self.orientation = 'right' if target_direction_x > 0 else 'left'
		else:
			pass

		# --- Calculate potential next position ---
		potential_next_pos_x = self.pos.x + target_direction_x * self.speed * dt
		potential_next_rect = self.rect.copy()
		potential_next_rect.x = round(potential_next_pos_x)

		# --- Check Boundaries and Obstacles ---
		final_direction_x = target_direction_x
		turn_around = False

		# 1. Patrol Boundaries
		patrol_left_limit = self.patrol_center_x - self.patrol_radius
		patrol_right_limit = self.patrol_center_x + self.patrol_radius
		next_center_x = potential_next_rect.centerx

		if next_center_x < patrol_left_limit:
			potential_next_rect.left = patrol_left_limit - potential_next_rect.width / 2 # Snap
			final_direction_x = 0 if self.is_alerted else 1 # Stop if chasing, turn if patrolling
			if not self.is_alerted: turn_around = True; self.orientation = 'right'
		elif next_center_x > patrol_right_limit:
			potential_next_rect.right = patrol_right_limit + potential_next_rect.width / 2 # Snap
			final_direction_x = 0 if self.is_alerted else -1 # Stop if chasing, turn if patrolling
			if not self.is_alerted: turn_around = True; self.orientation = 'left'

		# 2. Wall Collision Check
		for sprite in self.collision_sprites:
			if sprite.rect.colliderect(potential_next_rect):
				if target_direction_x > 0: # Moving right hit wall
					potential_next_rect.right = sprite.rect.left
					final_direction_x = -1 # Turn around
					turn_around = True
				elif target_direction_x < 0: # Moving left hit wall
					potential_next_rect.left = sprite.rect.right
					final_direction_x = 1 # Turn around
					turn_around = True
				self.pos.x = potential_next_rect.x # Update internal pos after collision adjustment
				break # Stop checking walls

		check_offset_x = TILE_SIZE / 2 * final_direction_x if final_direction_x != 0 else 0
		floor_check_pos = vector(potential_next_rect.centerx + check_offset_x, potential_next_rect.bottom + 5)
		has_floor_ahead = any(sprite.rect.collidepoint(floor_check_pos) for sprite in self.collision_sprites)

		if not has_floor_ahead and final_direction_x != 0: 
			if self.is_alerted:
				final_direction_x = 0 
			else: 
				final_direction_x *= -1 
				turn_around = True
				potential_next_rect.x = self.rect.x # Stay put horizontally

		self.pos.x = potential_next_rect.x
		self.rect.x = round(self.pos.x)
		self.direction.x = final_direction_x # Set direction for next frame
		if turn_around: # Update orientation if turned
			self.orientation = 'right' if self.direction.x > 0 else 'left'

	def update(self, dt):
		self.hit_timer.update()
		self.get_status() 
		self.move(dt)    
		self.animate(dt)
		self.update_attack_rect()

	def damage(self, amount, direction=None):
		if self.is_alive and not self.hit_timer.active:
			self.health -= amount
			self.hit_timer.activate()
			self.frame_index = 0
			if self.health <= 0:
				self.is_alive = False; self.frame_index = 0

	def draw_small_health_bar(self, surface, offset):
		if self.is_alive:
			bar_pos = self.rect.topleft - offset - vector(10, 20)
			bar_rect = self.bar_surf.get_rect(topleft=bar_pos)
			health_ratio = max(0, self.health / 10)
			red_width = self.red_surf.get_width() * health_ratio
			red_crop_rect = pygame.Rect(0, 0, red_width, self.red_surf.get_height())
			red_draw_pos = self.red_surf.get_rect(center=bar_rect.center)
			surface.blit(self.bar_surf, bar_rect)
			surface.blit(self.red_surf, red_draw_pos, red_crop_rect)

class Shell(Generic):
	def __init__(self, orientation, assets, pos, group, pearl_surf, pearl_destroyed, damage_sprites, health_bar_assets, attackable_sprites_group, collision_sprites):
		self.orientation = orientation
		self.animation_frames = assets.copy()
		if orientation == 'right':
			for key, value in self.animation_frames.items():
				self.animation_frames[key] = [pygame.transform.flip(surf,True,False) for surf in value]

		self.frame_index = 0
		self.status = 'idle'
		# Ensure initial animation exists
		init_key = self.status
		if init_key not in self.animation_frames or not self.animation_frames[init_key]:
			print(f"ERROR: Missing initial Shell animation '{init_key}'!")
			fallback_surf = pygame.Surface((TILE_SIZE, TILE_SIZE)); fallback_surf.fill('blue')
			self.animation_frames[init_key] = [fallback_surf]

		super().__init__(pos, self.animation_frames[self.status][self.frame_index], group)
		self.rect.bottom = self.rect.top + TILE_SIZE

		self.drawing_group = group[0]
		self.collision_sprites = collision_sprites
		self.health = 10
		self.hit_timer = Timer(250)
		self.is_alive = True
		self.bar_surf = health_bar_assets['bar']
		self.red_surf = health_bar_assets['red']
		self.pearl_surf = pearl_surf
		self.pearl_destroyed = pearl_destroyed
		self.has_shot = False
		self.attack_cooldown = Timer(2000)
		self.damage_sprites = damage_sprites
		self.attackable_sprites = attackable_sprites_group

	def damage(self, amount, direction=None):
		if not self.hit_timer.active and self.is_alive:
			self.health -= amount
			self.hit_timer.activate()
			self.frame_index = 0
			if self.health <= 0:
				self.is_alive = False; self.frame_index = 0; self.status = 'destroyed'

	def create_broken_shell(self):
		destroyed_frames = self.animation_frames.get('destroyed', []) # Use .get() for safety
		if len(destroyed_frames) < 5: print("ERROR: Shell 'destroyed' animation incomplete!"); self.kill(); return # Kill if cannot break
		tl, tr, br, bl = destroyed_frames[1], destroyed_frames[2], destroyed_frames[3], destroyed_frames[4]
		piece_w, piece_h = tl.get_size(); gap = 4
		new_surf = pygame.Surface((piece_w * 2 + gap, piece_h * 2 + gap), pygame.SRCALPHA)
		# Blit pieces based on orientation
		if self.orientation == 'left':
			new_surf.blit(tl, (0, 0)); new_surf.blit(tr, (piece_w + gap, 0))
			new_surf.blit(bl, (0, piece_h + gap)); new_surf.blit(br, (piece_w + gap, piece_h + gap))
		else:
			new_surf.blit(tr, (0, 0)); new_surf.blit(tl, (piece_w + gap, 0))
			new_surf.blit(br, (0, piece_h + gap)); new_surf.blit(bl, (piece_w + gap, piece_h + gap))
		FallingShell(self.rect.center, new_surf, self.drawing_group, self.collision_sprites)
		self.kill()

	def draw_small_health_bar(self, surface, offset):
		if self.is_alive:
			# Draw health bar
			bar_pos = self.rect.topleft - offset - vector(10, 20)
			bar_rect = self.bar_surf.get_rect(topleft = bar_pos)
			health_ratio = max(0, self.health / 10)
			red_width = self.red_surf.get_width() * health_ratio
			red_crop_rect = pygame.Rect(0, 0, red_width, self.red_surf.get_height())
			red_draw_rect = self.red_surf.get_rect(center = bar_rect.center)
			surface.blit(self.bar_surf, bar_rect)
			surface.blit(self.red_surf, red_draw_rect, red_crop_rect)


	def animate(self, dt):
		# Ensure status key exists
		if self.status not in self.animation_frames:
			print(f"ERROR: Missing Shell animation for status '{self.status}'!");
			self.status = 'idle' # Fallback to idle
			if 'idle' not in self.animation_frames: return # Cannot animate if idle is missing too

		current_animation = self.animation_frames[self.status]
		if not current_animation: return # Skip if animation list is empty

		# Handle 'destroyed' state
		if self.status == 'destroyed':
			self.frame_index += ANIMATION_SPEED * dt
			if int(self.frame_index) == 0:
				if current_animation: self.image = current_animation[0] # Show crack frame
			elif self.frame_index >= 1:
				self.create_broken_shell() # This kills the shell
			return

		# Handle other states
		self.frame_index += ANIMATION_SPEED * dt
		if self.frame_index >= len(current_animation):
			self.frame_index = 0
			if self.has_shot: self.attack_cooldown.activate(); self.has_shot = False

		if self.alive() and int(self.frame_index) < len(current_animation):
			self.image = current_animation[int(self.frame_index)]

		# Pearl shooting logic...
		if self.status == 'attack' and int(self.frame_index) == 2 and not self.has_shot and self.is_alive:
			pearl_direction = vector(-1,0) if self.orientation == 'left' else vector(1,0)
			offset = (pearl_direction * 50) + vector(0,-10) if self.orientation == 'left' else (pearl_direction * 20) + vector(0,-10)
			Pearl(self.rect.center + offset, pearl_direction, self.pearl_surf, [self.drawing_group, self.damage_sprites, self.attackable_sprites], self.pearl_destroyed)
			self.has_shot = True

	def get_status(self):
		# Priority: dead > hit > attack > idle
		if not self.is_alive: self.status = 'destroyed'
		elif self.hit_timer.active: self.status = 'hit'
		elif self.player and vector(self.player.rect.center).distance_to(self.rect.center) < 500 and not self.attack_cooldown.active:
			self.status = 'attack'
		else: self.status = 'idle'

	def update(self, dt):
		self.hit_timer.update()
		self.attack_cooldown.update()
		self.get_status() # Determine state first
		self.animate(dt)  # Animate based on state (handles destroy/kill)

class FallingShell(Generic):
	def __init__(self, pos, surf, group, collision_sprites):
		super().__init__(pos, surf, group)
		self.rect = self.image.get_rect(center = pos)
		self.pos = vector(self.rect.topleft)
		self.direction = vector(0, 0.5)
		self.speed = 400
		self.gravity = 0.8
		self.on_floor = False
		self.fade_timer = Timer(1500)
		self.collision_sprites = collision_sprites

	def apply_physics(self, dt):
		if not self.on_floor:
			self.direction.y += self.gravity * dt
			# Limit falling speed (optional)
			# self.direction.y = min(self.direction.y, 15)
			self.pos.y += self.direction.y # Apply speed in update if needed, gravity adds velocity here
			self.rect.y = round(self.pos.y)

			# Floor collision...
			for sprite in self.collision_sprites:
				if sprite.rect.colliderect(self.rect):
					if self.direction.y > 0:
						self.rect.bottom = sprite.rect.top
						self.pos.y = self.rect.y
						self.on_floor = True
						self.direction.y = 0
						self.fade_timer.activate()
						break

	def update(self, dt):
		self.apply_physics(dt * self.speed) # Apply speed scaling here
		self.fade_timer.update()
		if self.fade_timer.active:
			new_alpha = max(0, self.image.get_alpha() - 5)
			self.image.set_alpha(new_alpha)
			if new_alpha == 0: self.kill()

class Pearl(Generic):
	def __init__(self, pos, direction, surf, group, destroyed_assets):
		super().__init__(pos, surf, group)
		self.mask = pygame.mask.from_surface(self.image)
		self.pos = vector(self.rect.topleft)
		self.direction = direction.normalize()
		self.speed = 150
		self.is_alive = True
		self.destroyed_assets = destroyed_assets if destroyed_assets else [] # Safety check
		self.frame_index = 0
		self.has_split = False
		self.all_sprites_group = group[0]
		self.damage_group = group[1]
		self.attackable_group = group[2]
		self.timer = Timer(6000); self.timer.activate()

	def damage(self, amount):
		if self.is_alive:
			self.is_alive = False
			self.frame_index = 0
			self.remove(self.attackable_group, self.damage_group)

	def animate_destruction(self, dt):
		# Ensure assets exist
		if not self.destroyed_assets or len(self.destroyed_assets) < 3:
			print("ERROR: Pearl destroyed assets missing or incomplete!"); self.kill(); return

		self.frame_index += ANIMATION_SPEED * dt
		int_frame = int(self.frame_index)
		# Animate split and fade...
		if int_frame == 0: self.image = self.destroyed_assets[0]
		elif int_frame == 1 and not self.has_split:
			top, bottom = self.destroyed_assets[1], self.destroyed_assets[2]
			w, h_top = top.get_size(); _, h_bottom = bottom.get_size()
			new_surf = pygame.Surface((w, h_top + h_bottom + 5), pygame.SRCALPHA)
			new_surf.blit(top, (0, 0)); new_surf.blit(bottom, (0, h_top + 5))
			self.image = new_surf
			self.rect = self.image.get_rect(center = self.rect.center)
			self.has_split = True
		elif self.frame_index >= 2:
			new_alpha = max(0, self.image.get_alpha() - 15); self.image.set_alpha(new_alpha)
			if new_alpha == 0: self.kill()


	def update(self, dt):
		if self.is_alive:
			self.pos += self.direction * self.speed * dt
			self.rect.topleft = round(self.pos.x), round(self.pos.y)
			self.timer.update()
			if not self.timer.active: self.damage(0)
		else:
			self.animate_destruction(dt)

class Player(Generic):
	def __init__(self, pos, assets, group, collision_sprites, jump_sound):
		# Animation setup
		self.animation_frames = assets
		self.frame_index = 0
		self.status = 'idle'
		self.prev_status = self.status
		self.orientation = 'right'
		surf = self.animation_frames[f'{self.status}_{self.orientation}'][self.frame_index]
		super().__init__(pos, surf, group)
		self.mask = pygame.mask.from_surface(self.image)

		# Movement 
		self.direction = vector()
		self.pos = vector(self.rect.center)
		self.speed = 300
		self.gravity = 4 
		self.on_floor = False
  
		# Inventory
		self.inventory = {}
		self.coin_counts = {'gold': 0, 'silver': 0, 'diamond': 0}
  
		# Health
		self.health = 30 
		self.max_health = 30 

		# Collision
		self.collision_sprites = collision_sprites
		self.hitbox = self.rect.inflate(-50,0)

		# Timers
		self.invul_timer = Timer(200) # Original timer

		# Sound
		self.jump_sound = jump_sound
		self.jump_sound.set_volume(0.2) # Original volume

		# Air Attack / Attack
		self.attack_timer = Timer(400) 
		self.jump_height = -2 

	def damage(self, amount): 
		if not self.invul_timer.active:
			self.health -= amount # Use the amount parameter
			self.invul_timer.activate()
			self.direction.y -= 1.5

	def get_status(self):
		# Re-add air-attack differentiation
		if self.attack_timer.active:
			self.status = 'air-attack' if not self.on_floor else 'attack'
		elif self.direction.y < 0:
			self.status = 'jump'
		elif self.direction.y > 1:
			self.status = 'fall'
		else:
			self.status = 'run' if self.direction.x != 0 else 'idle'

	def animate(self, dt):
		# Make sure to handle the new air-attack status
		animation_key = f'{self.status}_{self.orientation}'
		if animation_key not in self.animation_frames:
			# Fallback if air-attack animation is missing
			if self.status == 'air-attack':
				animation_key = f'attack_{self.orientation}'
				if animation_key not in self.animation_frames:
					animation_key = f'idle_{self.orientation}' # Final fallback
			else: # Fallback for other missing animations
				animation_key = f'idle_{self.orientation}'

		if animation_key not in self.animation_frames: return # Can't animate

		current_animation = self.animation_frames[animation_key]
		self.frame_index += ANIMATION_SPEED * dt
		self.frame_index %= len(current_animation)
		self.image = current_animation[int(self.frame_index)]
		self.mask = pygame.mask.from_surface(self.image)

		if self.invul_timer.active:
			surf = self.mask.to_surface(); surf.set_colorkey('black')
			self.image = surf

	def input(self):
		keys = pygame.key.get_pressed()
		if keys[pygame.K_RIGHT]:
			self.direction.x = 1; self.orientation = 'right'
		elif keys[pygame.K_LEFT]:
			self.direction.x = -1; self.orientation = 'left'
		else:
			self.direction.x = 0

		if keys[pygame.K_SPACE] and self.on_floor:
			self.direction.y = -2 # Original jump value
			self.jump_sound.play()
   
	# Need start_attack to trigger the timer
	def start_attack(self):
		if not self.attack_timer.active:
			self.attack_timer.activate()

	def move(self, dt):
		# horizontal movement
		self.pos.x += self.direction.x * self.speed * dt
		self.hitbox.centerx = round(self.pos.x)
		self.rect.centerx = self.hitbox.centerx
		self.collision('horizontal')

		# vertical movement (apply gravity separately)
		self.pos.y += self.direction.y * self.speed * dt
		self.hitbox.centery = round(self.pos.y)
		self.rect.centery = self.hitbox.centery
		self.collision('vertical')

	def apply_gravity(self, dt):
		self.direction.y += self.gravity * dt
		self.rect.y += self.direction.y

	def check_on_floor(self):
		floor_rect = pygame.Rect(self.hitbox.bottomleft,(self.hitbox.width,2))
		floor_sprites = [sprite for sprite in self.collision_sprites if sprite.rect.colliderect(floor_rect)]
		self.on_floor = True if floor_sprites else False

	def collision(self, direction):
		for sprite in self.collision_sprites:
			if sprite.rect.colliderect(self.hitbox):
				if direction == 'horizontal':
					self.hitbox.right = sprite.rect.left if self.direction.x > 0 else self.hitbox.right
					self.hitbox.left = sprite.rect.right if self.direction.x < 0 else self.hitbox.left
					self.rect.centerx, self.pos.x = self.hitbox.centerx, self.hitbox.centerx
				else: # vertical
					self.hitbox.top = sprite.rect.bottom if self.direction.y < 0 else self.hitbox.top

					if self.direction.y > 0:
						self.hitbox.bottom = sprite.rect.top
						self.rect.bottom = self.hitbox.bottom 
					self.pos.y = self.hitbox.centery # Update pos from new hitbox position
					self.direction.y = 0 

	def update(self, dt):
		self.input()
		self.apply_gravity(dt) # Original update order
		self.move(dt)
		self.check_on_floor()
		self.invul_timer.update()
		self.attack_timer.update() # Update attack timer
		self.get_status()
		self.animate(dt)

# --- Crabby Class ---
class Crabby(Generic):
	def __init__(self, assets, pos, group, collision_sprites, item_sprites, attackable_sprites, boss_health_bar_assets, player, hit_sound, anchor='topleft'):
		# General setup
		self.animation_frames = assets
		self.frame_index = 0
		self.status = 'idle'
		self.orientation = 'left'
		# Initial animation key check
		init_key = f'{self.status}_{self.orientation}'
		if init_key not in self.animation_frames: init_key = 'idle_left'; self.orientation = 'left' # Fallback
		if init_key not in self.animation_frames: # Still missing?
			dummy = pygame.Surface((TILE_SIZE, TILE_SIZE)); dummy.fill('orange')
			self.animation_frames = {init_key: [dummy]}
		surf = self.animation_frames[init_key][self.frame_index]

		# Init with anchor...
		temp_sprite = pygame.sprite.Sprite(); temp_sprite.image = surf
		temp_sprite.rect = temp_sprite.image.get_rect(**{anchor: pos})
		super().__init__(temp_sprite.rect.topleft, surf, group)
		self.mask = pygame.mask.from_surface(self.image)

		# Position tracking...
		self.original_pos = vector(pos) if anchor == 'midbottom' else vector(self.rect.midbottom)
		self.pos = vector(self.rect.center)
		self.direction = vector()

		# Movement & Collision groups...
		self.speed = 90
		self.collision_sprites = collision_sprites
		self.item_sprites = item_sprites
		self.attackable_sprites_group = attackable_sprites

		# Health and damage...
		self.health = 30
		self.max_health = 30
		self.damage_amount = 3
		self.is_alive = True
		self.bar_surf = boss_health_bar_assets['bar']
		self.red_surf = boss_health_bar_assets['red']
  
		self.hit_sound = hit_sound

		# AI and interaction...
		self.player = player
		area_center_x = self.original_pos.x; area_center_y = self.original_pos.y - TILE_SIZE
		self.boss_area = pygame.Rect(0, 0, 800, 600); self.boss_area.center = (area_center_x, area_center_y)
		self.attack_timer = Timer(randint(3000, 4000))
		self.attack_duration_timer = Timer(600)
		self.attack_rect = pygame.Rect(0, 0, 70, self.rect.height - 20)
		self.has_attacked_this_swing = False

		# Add to damage_sprites group...
		if self in group:
			group_list = self.groups(); damage_group_index = 3
			if len(group_list) > damage_group_index and group_list[damage_group_index]:
				try: self.add(group_list[damage_group_index])
				except Exception as e: print(f"Error adding Crabby to damage_sprites: {e}")

	def get_status(self):
		if not self.is_alive:
			if self.status != 'dead-hit': 
				self.frame_index = 0; 
				self.status = 'dead-hit'
			return
		if self.status == 'hit': return 

		# If NOT dead or hit, determine AI state
		if not self.player: return

		player_in_area = self.boss_area.colliderect(self.player.rect)
		current_midbottom = vector(self.rect.midbottom)
		distance_to_origin = current_midbottom.distance_to(self.original_pos)
		next_status = self.status

		if player_in_area:
			# Player IN area - Run, Attack logic
			if self.status == 'idle' or self.status == 'return':
				next_status = 'run'
				if not self.attack_timer.active and not self.attack_duration_timer.active:
					self.attack_timer.duration = randint(3000, 4000); 
					self.attack_timer.activate()
			elif self.status == 'run':
				if not self.attack_timer.active:
					next_status = 'attack'; self.attack_duration_timer.activate()
			elif self.status == 'attack':
				if not self.attack_duration_timer.active:
					next_status = 'run'
					self.attack_timer.duration = randint(3000, 4000)
					self.attack_timer.activate()
		else:
			# Player OUTSIDE area - Return, Idle logic
			if distance_to_origin > 5:
				if self.status != 'return': next_status = 'return'
			else: 
				if self.status == 'return' or self.status != 'idle':
					next_status = 'idle'
					self.attack_timer.deactivate()
					if self.status == 'return': 
						self.rect.midbottom = self.original_pos
						self.pos = vector(self.rect.center)

		if next_status != self.status:
			self.status = next_status
			self.frame_index = 0 
			self.has_attacked_this_swing = False

	def get_orientation(self):
		if not self.is_alive or self.status in ('hit', 'idle'): return

		target_x = self.rect.centerx
		if self.status in ('run', 'attack') and self.player: target_x = self.player.rect.centerx
		elif self.status == 'return': target_x = self.original_pos.x

		direction_x = target_x - self.rect.centerx
		if abs(direction_x) > 10: 
			self.orientation = 'right' if direction_x > 0 else 'left'

	def move(self, dt):
		# Only move if alive AND status is 'run' or 'return'
		if not self.is_alive or self.status not in ('run', 'return'):
			self.direction.x = 0
			if self.status == 'idle' and vector(self.rect.midbottom) != self.original_pos:
				self.rect.midbottom = self.original_pos
				self.pos = vector(self.rect.center)
			return

		# Movement logic
		target_x = self.rect.centerx; move_amount = self.speed * dt
		if self.status == 'run':
			self.direction.x = 1 if self.orientation == 'right' else -1; target_x += self.direction.x * move_amount
		elif self.status == 'return':
			original_center_x = self.original_pos.x
			diff_x = original_center_x - self.rect.centerx
			if abs(diff_x) < move_amount: 
				target_x = original_center_x
				self.direction.x = 0
			else: 
				self.direction.x = 1 if diff_x > 0 else -1
				target_x += self.direction.x * move_amount

		# Apply Horizontal Movement & Collision
		self.rect.centerx = round(target_x)
		self.pos.x = self.rect.centerx
		obstacle_groups = [self.collision_sprites, self.item_sprites, self.attackable_sprites_group]
		collided = False 
		for group in obstacle_groups:
			for sprite in group:
				if sprite is not self and sprite.rect.colliderect(self.rect):
					if self.direction.x > 0: self.rect.right = sprite.rect.left
					elif self.direction.x < 0: self.rect.left = sprite.rect.right
					self.pos.x = self.rect.centerx
					self.direction.x = 0
					collided = True
					break
			if collided: break

		# Vertical Position
		self.rect.midbottom = (self.rect.centerx, self.original_pos.y)
		self.pos.y = self.rect.centery

	def animate(self, dt):
		# Determine animation key
		animation_status = self.status
		if self.status == 'return': animation_status = 'run'
		animation_key = f'{animation_status}_{self.orientation}'
		if self.status == 'hit': animation_key = f'hit_{self.orientation}'
		if not self.is_alive: animation_key = f'dead-hit_{self.orientation}'

		# Fallback
		if animation_key not in self.animation_frames:
			fallback_key_idle = f'idle_{self.orientation}'
			fallback_key_run = f'run_{self.orientation}'
			if fallback_key_idle in self.animation_frames: animation_key = fallback_key_idle
			elif fallback_key_run in self.animation_frames: animation_key = fallback_key_run
			else: print(f"ERROR: Missing animation key '{animation_key}' for Crabby!"); return

		current_animation = self.animation_frames[animation_key]
		self.frame_index += ANIMATION_SPEED * dt

		# Handle animation end / looping
		animation_finished = self.frame_index >= len(current_animation)

		if animation_finished:
			if not self.is_alive: # Dead fade
				self.frame_index = len(current_animation) - 1
				new_alpha = max(0, self.image.get_alpha() - 5); self.image.set_alpha(new_alpha)
				if new_alpha == 0: self.kill()
			# --- Transition out of HIT state when animation ends ---
			elif self.status == 'hit':
				self.frame_index = 0
				self.get_status()
				if self.status == 'hit':
					if self.player and self.boss_area.colliderect(self.player.rect):
						self.status = 'run' # Default to run if player is near
						if not self.attack_timer.active and not self.attack_duration_timer.active:
							self.attack_timer.duration = randint(3000, 4000); self.attack_timer.activate()
					else:
						# Player outside area, determine if should return or idle
						current_midbottom = vector(self.rect.midbottom)
						distance_to_origin = current_midbottom.distance_to(self.original_pos)
						if distance_to_origin > 5: self.status = 'return'
						else: self.status = 'idle'

				animation_status = self.status
				if self.status == 'return': animation_status = 'run'
				animation_key = f'{animation_status}_{self.orientation}'
				if animation_key not in self.animation_frames: # Fallback for the new state
					animation_key = f'idle_{self.orientation}' if f'idle_{self.orientation}' in self.animation_frames else list(self.animation_frames.keys())[0]
				current_animation = self.animation_frames.get(animation_key, [self.image]) # Use current image if key fails

			else: 
				self.frame_index = 0

		safe_index = max(0, int(self.frame_index))
		if self.alive() and safe_index < len(current_animation):
			self.image = current_animation[safe_index]
			self.mask = pygame.mask.from_surface(self.image)


	def update_attack_rect(self):
		if self.orientation == 'right': self.attack_rect.midleft = self.rect.midright + vector(-10, -10)
		else: self.attack_rect.midright = self.rect.midleft + vector(10, -10)

	def check_attack(self):
		if self.status == 'attack' and self.is_alive and int(self.frame_index) == 1:
			self.update_attack_rect()
			if self.attack_rect.colliderect(self.player.hitbox) and not self.player.invul_timer.active and not self.has_attacked_this_swing:
				if self.hit_sound: self.hit_sound.play()
				self.player.damage(self.damage_amount)
				self.has_attacked_this_swing = True

	def damage(self, amount, direction=None):
		if self.is_alive and self.status != 'hit':
			self.health -= amount
			self.frame_index = 0
			self.status = 'hit'
			if self.health <= 0:
				self.is_alive = False; self.frame_index = 0; self.status = 'dead-hit'

	def draw_boss_health_bar(self, surface, offset):
		if self.is_alive:
			bar_pos = self.rect.topleft - offset - vector(self.bar_surf.get_width() / 4 - 15, 30)    
			bar_rect = self.bar_surf.get_rect(topleft=bar_pos)
			health_ratio = max(0, self.health / self.max_health)
			red_width = self.red_surf.get_width() * health_ratio
			red_crop_rect = pygame.Rect(0, 0, red_width, self.red_surf.get_height())
			red_draw_pos = (bar_rect.left + 34,
							bar_rect.top + (self.bar_surf.get_height() - self.red_surf.get_height()) // 2 - 2)
			surface.blit(self.bar_surf, bar_rect)
			surface.blit(self.red_surf, red_draw_pos, red_crop_rect)

	def update(self, dt):
		self.attack_timer.update()
		self.attack_duration_timer.update()

		self.get_status() 
		self.get_orientation() 
		self.move(dt) 
		self.check_attack()
		self.animate(dt)