import pygame
from settings import *

class Inventory:
	def __init__(self, player, inventory_assets):
		self.player = player
		self.display_surface = pygame.display.get_surface()
		self.visible = False

		# Tải hình ảnh và font chữ
		self.cell_surf = inventory_assets['cell']
		self.item_surfs = inventory_assets['items']
		self.font = pygame.font.Font(None, 24)
  
		self.selection_index = 0
		self.selection_timer = pygame.time.get_ticks()
		self.can_move = True

	def toggle(self):
		self.visible = not self.visible
  
	def input(self):
		keys = pygame.key.get_pressed()

		if not self.can_move: return
  
		if keys[pygame.K_RIGHT]:
			self.selection_index = (self.selection_index + 1) % 3
			self.can_move = False
			self.selection_timer = pygame.time.get_ticks()
		elif keys[pygame.K_LEFT]:
			self.selection_index = (self.selection_index - 1 + 3) % 3
			self.can_move = False
			self.selection_timer = pygame.time.get_ticks()
   
		if keys[pygame.K_f]:
			self.use_item()
			self.can_move = False
			self.selection_timer = pygame.time.get_ticks()

	def cooldown(self):
		if not self.can_move:
			if pygame.time.get_ticks() - self.selection_timer > 300: 
				self.can_move = True

	def use_item(self):
		inventory_list = list(self.player.inventory.keys())
		if self.selection_index < len(inventory_list):
			item_name = inventory_list[self.selection_index]
			
			# Logic sử dụng vật phẩm
			if item_name == 'red_potion':
				self.player.health = self.player.max_health
			elif item_name == 'blue_potion':
				self.player.max_health += 5
				self.player.health += 5 

			# Giảm số lượng hoặc xóa vật phẩm
			if item_name != 'key': # Chìa khóa không bị tiêu hao ở đây
				self.player.inventory[item_name] -= 1
				if self.player.inventory[item_name] <= 0:
					del self.player.inventory[item_name]
			
			# Sắp xếp lại túi đồ sau khi dùng
			self.player.inventory = {k: v for k, v in self.player.inventory.items()}

	def update(self):
		# Xử lý input và cooldown chỉ khi túi đồ đang hiển thị
		if self.visible:
			self.cooldown()
			self.input()

	def display(self):
		if not self.visible:
			return

		# Tính toán vị trí cho 3 ô túi đồ ở giữa dưới màn hình
		total_width = 3 * self.cell_surf.get_width() + 2 * 10 # 3 ô + 2 khoảng cách
		start_x = (WINDOW_WIDTH - total_width) / 2
		bottom_y = WINDOW_HEIGHT - 20 # Vị trí sát đáy màn hình

		# Lấy danh sách các vật phẩm người chơi đang có
		display_items = list(self.player.inventory.keys())

		# Vẽ các ô và vật phẩm
		for index in range(3):
			cell_x = start_x + index * (self.cell_surf.get_width() + 10)
			cell_rect = self.cell_surf.get_rect(bottomleft=(cell_x, bottom_y))
			self.display_surface.blit(self.cell_surf, cell_rect)

			if index < len(display_items):
				item_name = display_items[index]
				item_surf = self.item_surfs[item_name]
				item_rect = item_surf.get_rect(center=cell_rect.center)
				self.display_surface.blit(item_surf, item_rect)

				item_count = self.player.inventory[item_name]
				item_count_text = str(item_count)
				stroke_color = '#3e3546'
				text_color = (255, 255, 255)

				if item_count > 1:
					# text_surf = self.font.render(str(item_count), False, '#3e3546')
					# text_rect = text_surf.get_rect(bottomright=cell_rect.bottomright - pygame.math.Vector2(5, 5))
					# self.display_surface.blit(text_surf, text_rect)
					
					# Stroke
					stroke_offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
					for offset in stroke_offsets:
						stroke_surf = self.font.render(item_count_text, True, stroke_color)
						stroke_rect = stroke_surf.get_rect(bottomright=cell_rect.bottomright - pygame.math.Vector2(5, 5))
						stroke_rect.move_ip(offset)
						self.display_surface.blit(stroke_surf, stroke_rect)

					# Main text
					text_surf = self.font.render(item_count_text, True, text_color)
					text_rect = text_surf.get_rect(bottomright=cell_rect.bottomright - pygame.math.Vector2(5, 5))
					self.display_surface.blit(text_surf, text_rect)

			# Vẽ highlight cho ô được chọn
			if index == self.selection_index:
				pygame.draw.rect(self.display_surface, '#f5e669', cell_rect, 4, 4)