import pygame, os
from os import walk

def import_folder(path):
	surface_list = []

	# for folder_name, sub_folders, img_files in walk(path):
	# 	for image_name in img_files:
	# 		full_path = path + '/' + image_name
	# 		image_surf = pygame.image.load(full_path).convert_alpha()
	# 		surface_list.append(image_surf)
	# return surface_list
	# Check if the path exists to avoid errors
	if not os.path.exists(path):
		print(f"Warning: Asset path does not exist: {path}")
		return surface_list

	# Use walk to get files and sort them to ensure correct animation order
	for _, __, img_files in walk(path):
		for image in sorted(img_files):
			full_path = os.path.join(path, image)
			image_surf = pygame.image.load(full_path).convert_alpha()
			surface_list.append(image_surf)
		break # Only process the top-level folder

	return surface_list

def import_folder_dict(path):
	surface_dict = {}

	for folder_name, sub_folders, img_files in walk(path):
		for image_name in img_files:
			full_path = path + '/' + image_name
			image_surf = pygame.image.load(full_path).convert_alpha()
			surface_dict[image_name.split('.')[0]] = image_surf
			
	return surface_dict