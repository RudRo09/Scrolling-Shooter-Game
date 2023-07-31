import pygame
from pygame import mixer
import random
import os
import csv
import button

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(800 * .8)
fps = 60

# creating clock
clock = pygame.time.Clock()

# game variables
GRAVITY = 0.75
SCROLL_THRESH = 250

ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
MAX_LEVEL = 3

level = 1
screen_scroll = 0
bg_scroll = 0

# create soldier movement variable
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False

# for main menu
start_game = False
start_intro = False


# define colors
bg_color = (0, 128, 43)				#(50, 150, 120)
red = (128, 0, 0)
white = (255, 255, 255)
green = (0, 255, 0)
black = (0, 0, 0)

#define font
font = pygame.font.SysFont('Bauhaus 93', 20)
level_font = pygame.font.SysFont('Constantia', 35)

# screate screen surface
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Shafin’s 2D Shooter Game")

# load music and sounds
pygame.mixer.music.load('sound/music2.mp3')
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1, 0.0, 5000)

# sound effects
jump_fx = pygame.mixer.Sound('sound/jumpland.wav')
jump_fx.set_volume(0.5)

shot_fx = pygame.mixer.Sound('sound/shot.wav')
shot_fx.set_volume(0.3)

grenade_fx = pygame.mixer.Sound('sound/grenade.wav')
grenade_fx.set_volume(0.5)

thrown_fx = pygame.mixer.Sound('sound/thrown.wav')
thrown_fx.set_volume(0.3)

death_fx = pygame.mixer.Sound('sound/death.mp3')
death_fx.set_volume(0.2)

level_up_fx = pygame.mixer.Sound('sound/level_up.mp3')
level_up_fx.set_volume(0.5)




# load images
# background
pine1_surface = pygame.image.load('assets/background/pine1.png').convert_alpha()
pine2_surface = pygame.image.load('assets/background/pine2.png').convert_alpha()
mountain_surface = pygame.image.load('assets/background/mountain.png').convert_alpha()
sky_surface = pygame.image.load('assets/background/sky_cloud.png').convert_alpha()

# button image
start_surface = pygame.image.load('assets/start_btn.png').convert_alpha()
exit_surface = pygame.image.load('assets/exit_btn.png').convert_alpha()
restart_surface = pygame.image.load('assets/restart_btn.png').convert_alpha()




# store tiles in a list
image_list = []
for x in range(TILE_TYPES):
	img = pygame.image.load(f'assets/tile/{x}.png').convert_alpha()
	img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
	image_list.append(img)

bullet_surface = pygame.image.load('assets/icons/bullet.png').convert_alpha()
grenade_surface = pygame.image.load('assets/icons/grenade.png').convert_alpha()
# pick up boxes
health_box_surface = pygame.image.load('assets/icons/health_box.png').convert_alpha()
ammo_box_surface = pygame.image.load('assets/icons/ammo_box.png').convert_alpha()
grenade_box_surface = pygame.image.load('assets/icons/grenade_box.png').convert_alpha()

item_boxes = {
	'Health' 	: health_box_surface,
	'Ammo'	 	: ammo_box_surface,
	'Grenade'	: grenade_box_surface
}


# drawing background function
def draw_bg():
	screen.fill(bg_color)
	width = sky_surface.get_width()
	for x in range(6):
		screen.blit(sky_surface, ((x * width) - bg_scroll * 0.5, 0))
		screen.blit(mountain_surface, ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - mountain_surface.get_height() - 300))
		screen.blit(pine1_surface, ((x * width) - bg_scroll * 0.7, SCREEN_HEIGHT - pine1_surface.get_height() - 150))
		screen.blit(pine2_surface, ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - pine2_surface.get_height() ))


# drawing text
def draw_text(text, font, text_col, x, y):
	font_surface = font.render(text, True, text_col)
	screen.blit(font_surface, (x, y))


def on_off():
	pygame.mixer.music.stop()
	death_fx.play()


# reset level
def reset_level():
	pygame.mixer.music.play(-1, 0.0, 5000)

	enemy_group.empty()
	bullet_group.empty()
	grenade_group.empty()
	explosion_group.empty()
	item_box_group.empty()
	decoration_group.empty()
	water_group.empty()
	exit_group.empty()

	# create empty tile list
	data = []
	for row in range(ROWS):
		r = [-1] * COLS
		data.append(r)

	return data


class Soldier(pygame.sprite.Sprite):
	def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
		pygame.sprite.Sprite.__init__(self)
		self.alive = True
		self.char_type = char_type
		self.speed = speed
		self.ammo = ammo
		self.max_ammo = self.ammo
		self.shoot_cooldown = 0
		self.grenades = grenades
		self.max_grenades = self.grenades
		self.health = 100
		self.max_health = self.health
		self.direction = 1
		self.vel_y = 0
		self.jump = False
		self.in_air = True
		self.flip = False
		self.animation_list = []
		self.frame_index = 0
		self.action = 0
		self.update_time = pygame.time.get_ticks()

		# variables for ai
		self.move_counter = 0
		self.vision = pygame.Rect(0, 0, 150, 20)
		self.idling = False
		self.idling_counter = 0

		# load all images for the players
		animation_types = ['Idle', 'Run', 'Jump', 'Death']
		for animation in animation_types:
			temp_list = []
			# count number of files in the folder
			num_of_frames = len(os.listdir(f'assets/{self.char_type}/{animation}'))
			for num in range(num_of_frames):
				player_surface = pygame.image.load(f'assets/{self.char_type}/{animation}/{num}.png').convert_alpha()
				player_surface = pygame.transform.scale(player_surface, (int(player_surface.get_width() * scale), int(player_surface.get_height() * scale)))
				temp_list.append(player_surface)

			self.animation_list.append(temp_list)

		self.animation_list.append(temp_list)
		self.image = self.animation_list[self.action][self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = [x, y]
		self.width = self.image.get_width()
		self.height = self.image.get_height()



	def update(self):
		self.update_animation()
		self.check_alive()
		if self.shoot_cooldown > 0:
			self.shoot_cooldown -= 1
	
	# soldier movement method
	def move(self, moving_left, moving_right):
		dx = 0
		dy = 0
		screen_scroll = 0
		# moving left and right
		if moving_left:
			dx = -self.speed
			self.flip = True
			self.direction = -1

		if moving_right:
			dx = self.speed
			self.flip = False
			self.direction = 1

		# jump
		if self.jump == True and not self.in_air:
			self.vel_y = -11
			self.jump = False
			self.in_air = True

		# apply gravity
		self.vel_y += GRAVITY
		if self.vel_y > 10:
			self.vel_y = 10

		dy += self.vel_y

		# check for collision
		for tile in world.obstacle_list:
			# check for collision in x direction
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				dx = 0

				# if ai has hit a wall - make him move around
				if self.char_type == 'enemy':
					self.direction *= 1
					self.move_counter = 0

			# check for collision in y direction
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				# if head hitting block
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top

				# landing on ground
				elif self.vel_y >= 0:
					self.vel_y = 0
					self.in_air = False
					dy = tile[1].top - self.rect.bottom


		# check for collision with water
		if pygame.sprite.spritecollide(self, water_group, False):
			self.health = 0
			on_off()

		# check for collision with exit
		level_complete = False
		if pygame.sprite.spritecollide(self, exit_group, False):
			level_complete = True


		# check for falling of map
		if self.rect.top > SCREEN_HEIGHT:
			self.health = 0
			on_off()

		# check if going off the screen
		if self.char_type == 'player':
			if self.rect.left + dx <= 0 or self.rect.right + dx > SCREEN_WIDTH:
				dx = 0


		# update rectangle position
		self.rect.x += dx
		self.rect.y += dy

		# update scroll based on player position
		if self.char_type == 'player':
			if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH) \
			or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
				self.rect.x -= dx
				screen_scroll = -dx

		return screen_scroll, level_complete

	def shoot(self):
		if self.shoot_cooldown == 0 and self.ammo > 0:
			self.shoot_cooldown = 16
			bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
			bullet_group.add(bullet)
			self.ammo -= 1
			shot_fx.play()


	# enemy ai for game
	def ai(self):
		if self.alive and player.alive:
			if not self.idling and random.randint(1, 200) == 1:
				self.update_action(0)
				self.idling = True
				self.idling_counter = 50
			# check if ai near player
			if self.vision.colliderect(player.rect):
				# stop running and fire player
				self.update_action(0)
				self.shoot()
			else:
				if not self.idling:
					if self.direction == 1:
						ai_moving_right = True
					else:
						ai_moving_right = False

					ai_moving_left = not ai_moving_right

					self.move(ai_moving_left, ai_moving_right)
					self.update_action(1)
					
					# make them move back n forward
					self.move_counter += 1
					# update ai vision
					self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)
					# pygame.draw.rect(screen, red, self.vision, 1)
					if self.move_counter > TILE_SIZE:
						self.direction *= -1
						self.move_counter *= - 1
				else:
					self.idling_counter -= 1
					if self.idling_counter <= 0:
						self.idling = False

		# scroll
		self.rect.x += screen_scroll


	# handle animation
	def update_animation(self):
		# define animation handling timer
		ANIMATION_COOLDOWN = 100
		time_now = pygame.time.get_ticks()
		self.image = self.animation_list[self.action][self.frame_index]

		if time_now - self.update_time > 100:			
			self.update_time = time_now
			self.frame_index += 1

		if self.frame_index >= len(self.animation_list[self.action]):
			if self.action == 3:
				self.frame_index = len(self.animation_list[self.action]) - 1
			
			else:
				self.frame_index = 0


	# handle action animation
	def update_action(self, new_action):
		if new_action != self.action:
			self.action = new_action
			# update animation settings
			self.frame_index = 0
			self.update_time = pygame.time.get_ticks()


	def check_alive(self):
		if self.health <= 0:
			self.health = 0
			self.speed = 0
			self.alive = False
			self.update_action(3)


	def draw(self):
		screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)
		#pygame.draw.rect(screen, red, self.rect, 1)


# world class
class World:
	def __init__(self):
		self.obstacle_list = []

	def process_data(self, data):
		self.level_length = len(data[0])		# to know how wide/long the level is
		# iterate through each value in data file
		for y, row in enumerate(data):
			for x, tile in enumerate(row):
				if tile >= 0:
					img = image_list[tile]
					img_rect = img.get_rect()
					img_rect.x = x * TILE_SIZE
					img_rect.y = y * TILE_SIZE
					tile_data = (img, img_rect)

					if tile >= 0 and tile <= 8:
						self.obstacle_list.append(tile_data)
					
					elif tile >= 9 and tile <= 10: # water
						water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
						water_group.add(water)   
					
					elif tile >= 11 and tile <= 14: # decoration 
						decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
						decoration_group.add(decoration)  

					elif tile == 15:  # create player
						player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 1.65, 5, 25, 5)
						health_bar = Healthbar(10, 10, player.health, player.health)

					elif tile == 16:  # create enemy
						enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 1.65, 2, 15, 0)
						enemy_group.add(enemy)

					elif tile == 17:  # create ammo box
						item_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)

					elif tile == 18:  # create grenade box
						item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)

					elif tile == 19:  # create health box
						item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)

					elif tile == 20: # create exit
						exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
						exit_group.add(exit) 

		return player, health_bar

	def draw(self):
		for tile in self.obstacle_list:
			tile[1][0] += screen_scroll
			screen.blit(tile[0], tile[1])


# water class
class Water(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))


	def update(self):
		self.rect.x += screen_scroll


# decoration class
class Decoration(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))


	def update(self):
		self.rect.x += screen_scroll

# Exit class
class Exit(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll


# item class
class ItemBox(pygame.sprite.Sprite):	
	def __init__(self, item_type, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.item_type = item_type		#key to access dictionary
		self.image = item_boxes[self.item_type]
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))


	def update(self):
		# scroll
		self.rect.x += screen_scroll
		# check if player has picked box (collision)
		if pygame.sprite.collide_rect(self, player):
			# check what type of box
			if self.item_type == 'Health':
				player.health += 25
				if player.health > player.max_health:
					player.health = player.max_health
			elif self.item_type == 'Ammo':
				player.ammo += 10
				if player.ammo > player.max_ammo:
					player.ammo = player.max_ammo
			elif self.item_type == 'Grenade':
				player.grenades += 3
				if player.grenades > player.max_grenades:
					player.grenades = player.max_grenades

			# delete itembox after pickup
			self.kill()


# health bar class
class Healthbar:
	def __init__(self, x, y, health, max_health):
		self.x = x
		self.y = y
		self.health = health
		self.max_health = max_health


	def draw(self, health):
		# update with new health
		self.health = health
		# calculate health ratio
		ratio = self.health / self.max_health
		pygame.draw.rect(screen, black, (self.x - 2, self.y - 2, 154, 24))
		pygame.draw.rect(screen, red, (self.x, self.y, 150, 20))
		pygame.draw.rect(screen, green, (self.x, self.y, 150 * ratio, 20))



# create Bullet class
class Bullet(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.speed = 10
		self.image = bullet_surface
		self.rect = self.image.get_rect()
		self.rect.center = [x, y]
		self.direction = direction


	def update(self):
		# move bullet
		self.rect.x += (self.direction * self.speed) + screen_scroll
		# check if bullet is out of screen
		if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
			self.kill()

		# check collision with walls
		for tile in world.obstacle_list:
			if tile[1].colliderect(self.rect):
				self.kill()


		# check collision with characters
		if pygame.sprite.spritecollide(player, bullet_group, False):
			if player.alive:
				player.health -= 5
				self.kill()
				if player.health <= 0:
					on_off()
		for enemy in enemy_group:
			if pygame.sprite.spritecollide(enemy, bullet_group, False):
				if enemy.alive:
					enemy.health -= 30
					self.kill()


# grenade class
class Grenade(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.timer = 100
		self.vel_y = -11
		self.speed = 7
		self.image = grenade_surface
		self.rect = self.image.get_rect()
		self.rect.center = [x, y]
		self.width = self.image.get_width()
		self.height = self.image.get_height()
		self.direction = direction


	def update(self):
		self.vel_y += GRAVITY
		dx = self.direction * self.speed
		dy = self.vel_y

		# check for collision with level
		for tile in world.obstacle_list:
			# check collision with walls
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				self.direction *= -1
				dx = self.direction * self.speed

		# check collision in y direction
		# check for collision in y diirection
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				self.speed = 0
				# check for collision when thrown up
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top

			# landing on ground
				elif self.vel_y >= 0:
					self.vel_y = 0
					dy = tile[1].top - self.rect.bottom


		# update grenade position
		self.rect.x += dx + screen_scroll
		self.rect.y += dy

		# fusing grenade/countdown timer
		self.timer -= 1
		if self.timer <= 0:
			self.kill()
			grenade_fx.play()
			explosion = Explosion(self.rect.x, self.rect.y, 0.7)
			explosion_group.add(explosion)
			# do damage to anyone that is nearby
			# check against player    					# I will update here ***
			if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and \
				abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
					player.health -= 100
					on_off()

			for enemy in enemy_group:
				if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and \
					abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
						enemy.health -= 100



# explosion class
class Explosion(pygame.sprite.Sprite):
	def __init__(self, x, y, scale):
		pygame.sprite.Sprite.__init__(self)
		self.exp_list = []
		self.frame_index = 0
		for num in range(1, 6):
			exp_surface = pygame.image.load(f'assets/explosion/exp{num}.png').convert_alpha()
			exp_surface = pygame.transform.scale(exp_surface, (int(exp_surface.get_width() * scale),\
						 int(exp_surface.get_height() * scale)))

			self.exp_list.append(exp_surface)

		self.image = self.exp_list[self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = [x, y]
		self.counter = 0


	# update explosion animation
	def update(self):
		# scroll			
		self.rect.x += screen_scroll
		EXPLOSION_SPEED = 4
		self.counter += 1
		if self.counter >= EXPLOSION_SPEED:
			self.counter = 0
			self.frame_index += 1
			# if animation is complete delete the explosion
			if self.frame_index >= len(self.exp_list):
				self.kill()
			else:
				self.image = self.exp_list[self.frame_index]


# screen transaction class
class ScreenFade:
	def __init__(self, direction, colour, speed):
		self.direction = direction
		self.colour = colour
		self.speed = speed
		self.fade_counter = 0


	def fade(self):
		fade_complete = False
		self.fade_counter += self.speed

		if self.direction == 1:		# whole screen fade
			pygame.draw.rect(screen, self.colour, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
			pygame.draw.rect(screen, self.colour, (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
			pygame.draw.rect(screen, self.colour, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
			pygame.draw.rect(screen, self.colour, (0, SCREEN_HEIGHT // 2 + self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))




		if self.direction == 2:		# vertical screen fade
			pygame.draw.rect(screen, self.colour, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
		if self.fade_counter >= SCREEN_WIDTH:
			fade_complete = True

		return fade_complete


# create screen fades object
intro_fade = ScreenFade(1, black, 4)
death_fade = ScreenFade(2, red, 4)


# create buttons
start_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_surface, 1)
exit_button = button.Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_surface, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_surface, 2)




# create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()


# create empty tile list
world_data = []
for row in range(ROWS):
	r = [-1] * COLS
	world_data.append(r)

# load in level data and create world
with open(f'level{level}_data.csv', newline= '') as csvfile:
	reader = csv.reader(csvfile, delimiter= ',')
	for x, row in enumerate(reader):
		for y, tile in enumerate(row):
			world_data[x][y] = int(tile)

world = World()
player, health_bar = world.process_data(world_data)

run = True
while run:

	clock.tick(fps)

	if not start_game:
		# draw menu
		screen.fill(bg_color)
		# add buttons
		if start_button.draw(screen):
			start_game = True
			start_intro = True

		if exit_button.draw(screen):
			run = False
	else:

		# update background
		draw_bg()

		# draw world map
		world.draw()

		# show player health
		health_bar.draw(player.health)
		# show ammo
		draw_text('AMMO: ', font, white, 10, 40)
		for x in range(player.ammo):
			screen.blit(bullet_surface, (90 + (x * 10), 45))

		# show grenades
		draw_text('GRENADES: ', font, white, 10, 65)
		for x in range(player.grenades):
			screen.blit(grenade_surface, (115 + (x * 15), 68))





		player.update()
		player.draw()

		for enemy in enemy_group:
			enemy.ai()
			enemy.update()
			enemy.draw()

		# draw and update sprite groups
		bullet_group.update()
		grenade_group.update()
		explosion_group.update()
		item_box_group.update()
		decoration_group.update()
		water_group.update()
		exit_group.update()


		bullet_group.draw(screen)
		grenade_group.draw(screen)
		explosion_group.draw(screen)
		item_box_group.draw(screen)
		decoration_group.draw(screen)
		water_group.draw(screen)
		exit_group.draw(screen)


		# show intro
		if start_intro:
			if intro_fade.fade():
				start_intro = False
				intro_fade.fade_counter = 0

		# update player action
		if player.alive:
			draw_text('level ' + str(level), level_font, white, (SCREEN_WIDTH // 2) - 45, 7)
			# shoot bullets
			if shoot:
				player.shoot()

			# throw grenades
			elif grenade and not grenade_thrown and player.grenades > 0:
				grenade = Grenade(player.rect.centerx +(0.5 * player.rect.size[0] * player.direction),\
								 player.rect.top, player.direction)
				grenade_group.add(grenade)
				grenade_thrown = True
				player.grenades -= 1

			if moving_left or moving_right:
				player.update_action(1)
			elif player.in_air:
				player.update_action(2)
			else:
				player.update_action(0)

			screen_scroll, level_complete = player.move(moving_left, moving_right)
			bg_scroll -= screen_scroll

			# check if player has completed the level
			if level_complete:
				start_intro = True
				level_up_fx.play()
				level += 1
				bg_scroll = 0
				world_data = reset_level()
				if level <= MAX_LEVEL:
					# load in level data and create world
					with open(f'level{level}_data.csv', newline= '') as csvfile:
						reader = csv.reader(csvfile, delimiter= ',')
						for x, row in enumerate(reader):
							for y, tile in enumerate(row):
								world_data[x][y] = int(tile)
				
					world = World()
					player, health_bar = world.process_data(world_data)


		else:
			screen_scroll = 0
			if death_fade.fade():
				if restart_button.draw(screen):
					death_fade.fade_counter = 0
					start_intro = True
					bg_scroll = 0
					world_data = reset_level()

					# load in level data and create world
					with open(f'level{level}_data.csv', newline= '') as csvfile:
						reader = csv.reader(csvfile, delimiter= ',')
						for x, row in enumerate(reader):
							for y, tile in enumerate(row):
								world_data[x][y] = int(tile)
					
					world = World()
					player, health_bar = world.process_data(world_data)




	# event handlers
	for event in pygame.event.get():
		# to quit game
		if event.type == pygame.QUIT:
			run = False

		# get key press
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_a:
				moving_left = True
			if event.key == pygame.K_d:
				moving_right = True
			if event.key == pygame.K_w and player.alive:
				player.jump = True
				jump_fx.play()
			if event.key == pygame.K_SPACE:
				shoot = True
			if event.key == pygame.K_g:
				grenade = True
				thrown_fx.play()
			if event.key == pygame.K_ESCAPE:
				run = False


		# get key release
		if event.type == pygame.KEYUP:
			if event.key == pygame.K_a:
				moving_left = False
			if event.key == pygame.K_d:
				moving_right = False
			if event.key == pygame.K_SPACE:
				shoot = False
			if event.key == pygame.K_g:
				grenade = False
				grenade_thrown = False



	pygame.display.update()

pygame.quit()