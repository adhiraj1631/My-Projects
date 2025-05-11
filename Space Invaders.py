import pygame
from pygame import mixer
import random
import os
import pyttsx3
import math
import tkinter as tk
from tkinter import simpledialog

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

# Define fps
clock = pygame.time.Clock()
fps = 60

# Screen settings
screen_width = 600
screen_height = 800
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Space Invaders')

# Define fonts
font30 = pygame.font.SysFont('Constantia', 30)
font40 = pygame.font.SysFont('Constantia', 40)
font60 = pygame.font.SysFont('Constantia', 60)  # Larger font for level display
font18 = pygame.font.SysFont('Constantia', 18) #small font for hints


# Load sounds
explosion_fx = pygame.mixer.Sound("explosion.wav")
explosion_fx.set_volume(0.25)

explosion2_fx = pygame.mixer.Sound("explosion2.wav")
explosion2_fx.set_volume(0.25)

laser_fx = pygame.mixer.Sound("laser.wav")
laser_fx.set_volume(0.25)

# Define colors
red = (255, 0, 0)
green = (0, 255, 0)
white = (255, 255, 255)
black = (0, 0, 0) # Black Color
grey = (200, 200, 200) # Grey color

# Load background image
bg = pygame.image.load("bg.png")

# Load heart image
heart_img = pygame.image.load("heart.jpg")
heart_img = pygame.transform.scale(heart_img, (20, 20))

# Initialize pyttsx3
engine = pyttsx3.init()
level_announced = False  # Variable to check if level is announced
game_over_announced = False  # variable to check if game over is announced
player_won = False  # Variable to track if the player won

# Get Player Name
def get_player_name():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    player_name = simpledialog.askstring("Space Invaders", "Please enter your name:",
                                         initialvalue="Player")  # Default name
    if player_name:
        return player_name
    else:
        return "Player"  # Default name if user cancels or enters nothing


player_name = get_player_name()

# Function to draw background
def draw_bg():
    screen.blit(bg, (0, 0))

# Function to draw text
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

# Create Explosion class
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, size):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 6):
            img = pygame.image.load(f"exp{num}.png")
            img = pygame.transform.scale(img, (20 * size, 20 * size))
            self.images.append(img)
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.counter = 0

    def update(self):
        explosion_speed = 3
        self.counter += 1

        if self.counter >= explosion_speed and self.index < len(self.images) - 1:
            self.counter = 0
            self.index += 1
            self.image = self.images[self.index]

        if self.index >= len(self.images) - 1 and self.counter >= explosion_speed:
            self.kill()


# Create Bullets class
class Bullets(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("bullet.png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]

    def update(self):
        self.rect.y -= 5
        if self.rect.bottom < 0:
            self.kill()

        # Check if bullet hits the AI Agent
        global ai_agent, score, player_won, game_over
        if ai_agent and pygame.sprite.spritecollide(self, ai_agent_group, False):
            self.kill()
            explosion_fx.play()
            explosion = Explosion(self.rect.centerx, self.rect.centery, 2)
            explosion_group.add(explosion)
            score -= 20  # Decrease player's score

            ai_agent.ai_agent_hit_count += 1
            remaining_lives = 5 - ai_agent.ai_agent_hit_count

            if remaining_lives >= 0:
                if remaining_lives==4 and not ai_agent.lives_announced[0]:
                    engine.say(f"Attention ! Defender hit! Remaining lives: {remaining_lives}")
                    engine.runAndWait()
                    ai_agent.lives_announced[0]=True
                elif remaining_lives==3 and not ai_agent.lives_announced[1]:
                    engine.say(f"Attention ! Defender hit! Remaining lives: {remaining_lives}")
                    engine.runAndWait()
                    ai_agent.lives_announced[1]=True
                elif remaining_lives==2 and not ai_agent.lives_announced[2]:
                    engine.say(f"Attention ! Defender hit! Remaining lives: {remaining_lives}")
                    engine.runAndWait()
                    ai_agent.lives_announced[2]=True
                elif remaining_lives==1 and not ai_agent.lives_announced[3]:
                    engine.say(f"Attention ! Defender hit! Remaining lives: {remaining_lives}")
                    engine.runAndWait()
                    ai_agent.lives_announced[3]=True

            if ai_agent.ai_agent_hit_count >= 5:
                game_over = True
                player_won = False
                engine.say(f"Mission Failed! {player_name}!")
                engine.runAndWait()
        # Update score when hitting an alien
        elif pygame.sprite.spritecollide(self, alien_group, True):
            self.kill()
            explosion_fx.play()
            explosion = Explosion(self.rect.centerx, self.rect.centery, 2)
            explosion_group.add(explosion)
            score += 10  # Increase score by 10
            if level == max_levels and len(alien_group) == 0:  # End game if level 5 is done
                player_won = True
                game_over = True


# Create Spaceship class
class Spaceship(pygame.sprite.Sprite):
    def __init__(self, x, y, health):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("spaceship.png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.health_start = health
        self.health_remaining = health
        self.last_shot = pygame.time.get_ticks()
        self.lives = 3  # Initialize lives here
        self.hit_time = 0  # Time when spaceship was last hit
        self.lives_announced = [False, False, False] # Track lives announcement

    def update(self):
        speed = 8
        cooldown = 500  # milliseconds
        global game_over  # Use the global game_over variable

        # Apply hit pause of 1 second
        if pygame.time.get_ticks() - self.hit_time < 1000:  # 1 sec = 1000 ms
            return  # Skip movement if hit

        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= speed
        if key[pygame.K_RIGHT] and self.rect.right < screen_width:
            self.rect.x += speed

        time_now = pygame.time.get_ticks()
        if key[pygame.K_SPACE] and time_now - self.last_shot > cooldown:
            laser_fx.play()
            bullet = Bullets(self.rect.centerx, self.rect.top)
            bullet_group.add(bullet)
            self.last_shot = time_now

        self.mask = pygame.mask.from_surface(self.image)

        pygame.draw.rect(screen, red, (self.rect.x, self.rect.bottom + 10, self.rect.width, 15))
        if self.health_remaining > 0:
            pygame.draw.rect(screen, green, (
                self.rect.x, self.rect.bottom + 10, int(self.rect.width * (self.health_remaining / self.health_start)),
                15))
        else:
            explosion = Explosion(self.rect.centerx, self.rect.centery, 3)
            explosion_group.add(explosion)
            self.kill()
            global player_won  # Access global plyaer_won
            player_won = False  # Player lost
            game_over = True  # Set game over to True
        return game_over

    def hit(self):  # Call this when player is hit
        self.hit_time = pygame.time.get_ticks()  # Mark current time

        if self.lives == 3 and not self.lives_announced[0]:
            self.lives -= 1
            engine.say(f"Spaceship hit ! Remaining lives: {self.lives}")
            engine.runAndWait()
            self.lives_announced[0] = True

        elif self.lives == 2 and not self.lives_announced[1]:
            self.lives -= 1
            engine.say(f"Spaceship hit ! Remaining lives: {self.lives}")
            engine.runAndWait()
            self.lives_announced[1] = True

        elif self.lives == 1 and not self.lives_announced[2]:
            self.lives -= 1
            engine.say(f"Spaceship hit ! Remaining lives: {self.lives}")
            engine.runAndWait()
            self.lives_announced[2] = True
        elif self.lives==0:
             game_over = True


# Create Aliens class
class Aliens(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("alien" + str(random.randint(1, 5)) + ".png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.move_counter = 0
        self.move_direction = 1
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 75:
            self.move_direction *= -1
            self.move_counter *= self.move_direction

        time_now = pygame.time.get_ticks()

        # Limit the number of alien bullets. Check bullet count BEFORE firing
        global alien_bullet_group
        if len(alien_bullet_group) < max_alien_bullets:  # Only fire is total bullets on screen < max
            if time_now - self.last_shot > random.randint(1000, 3000) - (level * 50):  # Firing rate increases
                bullet = Alien_Bullets(self.rect.centerx, self.rect.bottom, level,
                                       spaceship)  # Pass level to Alien_Bullets and spaceship
                alien_bullet_group.add(bullet)
                self.last_shot = time_now


# Create Alien Bullets class
class Alien_Bullets(pygame.sprite.Sprite):
    def __init__(self, x, y, level, spaceship, speed_multiplier=1.0):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("alien_bullet.png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.base_speed = 1.5 + (level * 0.3)  # Base speed + level scaling
        self.speed = self.base_speed * speed_multiplier  # Apply speed multiplier
        self.spaceship = spaceship  # Store the spaceship object

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > screen_height:
            self.kill()
        if pygame.sprite.spritecollide(self, spaceship_group, False, pygame.sprite.collide_mask):
            self.kill()
            explosion2_fx.play()
            self.spaceship.health_remaining -= 1  # Update lives of spaceship object and not of class
            self.spaceship.hit()  # Call to mark the player as hit
            explosion = Explosion(self.rect.centerx, self.rect.centery, 1)
            explosion_group.add(explosion)


# AI Agent Class
class AIAgent(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("ai (1).jpg")  # Use a different alien image
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.last_shot = pygame.time.get_ticks()
        self.cooldown = 375  # 0.25 times faster than the aliens (500 * 0.75)
        self.movement_speed = 4  # Normal speed
        self.ai_agent_hit_count = 0  # Resetting the hit count to 0
        self.burst_count = 0  # How many shots fired in the current burst
        self.burst_size = 30  # Fire 30 shots at a time
        self.burst_cooldown = 5000  # Pause of 5 seconds
        self.last_burst = pygame.time.get_ticks()  # When was the last time we started a burst?
        self.is_paused = False  # Is the AI paused?
        self.pause_start_time = 0  # When did the pause start?
        self.ai_hit_pause = False  # Flag to control pause
        self.ai_pause_start_time = 0  # Time the AI pause started
        self.lives_announced = [False, False, False, False]

    def predict_spaceship_position(self):
        # Very basic prediction - move towards where spaceship *will* be
        # based on its *current* direction.  More sophisticated solutions exist
        spaceship_x = spaceship.rect.centerx
        speed = 8  # Spaceship speed

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            spaceship_x -= speed
        if keys[pygame.K_RIGHT]:
            spaceship_x += speed
        spaceship_x = max(0, min(spaceship_x, screen_width))  # clamp

        return spaceship_x

    def update(self):

        # Burst fire logic
        time_now = pygame.time.get_ticks()

        # Move to predicted spaceship position.
        if spaceship.alive():
            target_x = self.predict_spaceship_position()
            if self.rect.centerx < target_x:
                self.rect.x += self.movement_speed
                self.attack()  # Call attack while moving
            elif self.rect.centerx > target_x:
                self.rect.x -= self.movement_speed
                self.attack()  # Call attack while moving

        if self.is_paused:
            if time_now - self.pause_start_time > self.burst_cooldown:  # 5 second pause
                self.is_paused = False
                self.last_burst = time_now  # Reset the burst timer
        else:
            if time_now - self.last_burst > 0:
                if self.burst_count < self.burst_size:
                    if time_now - self.last_shot > self.cooldown:  # Can we fire a shot?
                        # Increase the speed of bullet with level
                        speed_multiplier = 1.0 + (level * 0.05)  # 5% increase in speed per level
                        bullet = Alien_Bullets(self.rect.centerx, self.rect.bottom, level, spaceship, speed_multiplier)
                        alien_bullet_group.add(bullet)
                        self.last_shot = time_now
                        self.burst_count += 1  # increment shot count
                else:  # Burst is complete, reset
                    self.burst_count = 0  # reset the shot count
                    self.is_paused = True
                    self.pause_start_time = time_now

    def hit(self):  # Call this when ai agent is hit
        remaining_lives = 5 - self.ai_agent_hit_count
        if remaining_lives == 4 and not self.lives_announced[0]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[0] = True
        elif remaining_lives == 3 and not self.lives_announced[1]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[1] = True
        elif remaining_lives == 2 and not self.lives_announced[2]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[2] = True
        elif remaining_lives == 1 and not self.lives_announced[3]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[3] = True


    def attack(self):  # Function for the ai agent to start attacking
        time_now = pygame.time.get_ticks()
        if not self.is_paused:  # If it is paused, don't attack
            if time_now - self.last_burst > 0:
                if self.burst_count < self.burst_size:
                    if time_now - self.last_shot > self.cooldown:  # Can we fire a shot?
                        # Increase the speed of bullet with level
                        speed_multiplier = 1.0 + (level * 0.05)  # 5% increase in speed per level
                        bullet = Alien_Bullets(self.rect.centerx, self.rect.bottom, level, spaceship, speed_multiplier)
                        alien_bullet_group.add(bullet)
                        self.last_shot = time_now
                        self.burst_count += 1  # increment shot count
                else:  # Burst is complete, reset
                    self.burst_count = 0  # reset the shot count
                    self.is_paused = True
                    self.pause_start_time = time_now


# Function to create AI Agent
def create_ai_agent():
    global ai_agent
    ai_agent = AIAgent(screen_width // 2, 100 + 2 * 70)  # 3rd Row
    ai_agent_group.add(ai_agent)


# Create sprite groups
spaceship_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
alien_group = pygame.sprite.Group()
alien_bullet_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
ai_agent_group = pygame.sprite.Group()  # Group for ai agent

level = 1
max_levels = 5

# AI Agent variables
ai_agent = None

# Limit maximum alien bullets
max_alien_bullets = 5  # 5 bullets can be fired at a time

# Declare global variables before use
game_over = False
player_won = False
score = 0
last_hit = 0  # Time when player was last hit

# Game time variables
start_time = pygame.time.get_ticks()  # Get game start time

# Level control (starting)
level_start_time = 0
display_level_timer = 0
display_level_duration = 3  # Display level for 3 seconds
display_level = True  # Display Level at the start


def create_aliens():
    alien_group.empty()
    # Increase the number of rows and columns based on the level
    num_rows = level + 3  # Increased number of rows
    num_cols = level + 4  # Increased number of columns

    for row in range(num_rows):
        for col in range(num_cols):
            alien = Aliens(100 + col * 80, 100 + row * 60)  # adjusted x and y coordinates
            alien_group.add(alien)


# Initialize spaceship before calling create_ai_agent()
spaceship = Spaceship(int(screen_width / 2), screen_height - 100, 3)
spaceship_group.add(spaceship)

create_aliens()

# Get Ready Timer
get_ready_time = 3  # seconds
start_time = pygame.time.get_ticks()
game_started = False
countdown_number = 3

# Game start time
game_start_time = 0
game_end_time = 0  # Initialize game end time to zero for calcualting time


def reset_ai_agent():  # Creating reset function
    global ai_agent
    if ai_agent:
        ai_agent.kill()  # remove the ai agent
        ai_agent = None  # set it to none so as to reset all properties


#Mode 2
class Aliens2(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("alien" + str(random.randint(1, 5)) + ".png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.move_counter = 0
        self.move_direction = 1
        self.last_shot = pygame.time.get_ticks()
        self.x = float(x)  # Store x as float for smoother movement
        self.y = float(y) # Store y as float for smoother movement

    def update(self):
        self.x += self.move_direction * 0.5 #Small movements
        self.rect.x = int(self.x)

        self.move_counter += 1
        if abs(self.move_counter) > 75:
            self.move_direction *= -1
            self.move_counter *= self.move_direction

        time_now = pygame.time.get_ticks()

        # Limit the number of alien bullets. Check bullet count BEFORE firing
        global alien_bullet_group
        if len(alien_bullet_group) < max_alien_bullets:  # Only fire is total bullets on screen < max
            if time_now - self.last_shot > random.randint(1000, 3000) - (level * 50):  # Firing rate increases
                bullet = Alien_Bullets2(self.rect.centerx, self.rect.bottom, level,
                                       ai_spaceship)  # Pass level to Alien_Bullets and spaceship
                alien_bullet_group.add(bullet)
                self.last_shot = time_now

# Create Alien Bullets class
class Alien_Bullets2(pygame.sprite.Sprite):
    def __init__(self, x, y, level, spaceship, speed_multiplier=1.0):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("alien_bullet.png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.base_speed = 1.5 + (level * 0.3)  # Base speed + level scaling
        self.speed = self.base_speed * speed_multiplier  # Apply speed multiplier
        self.spaceship = spaceship  # Store the spaceship object

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > screen_height:
            self.kill()
        if pygame.sprite.spritecollide(self, ai_spaceship_group, False, pygame.sprite.collide_mask):
            self.kill()
            explosion2_fx.play()
            explosion = Explosion(self.rect.centerx, self.rect.centery, 1)
            explosion_group.add(explosion)
            ai_spaceship.hit()

# AI Agent Class
class AIAgent2(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("ai (1).jpg")  # Use a different alien image
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.last_shot = pygame.time.get_ticks()
        self.cooldown = 375  # 0.25 times faster than the aliens (500 * 0.75)
        self.movement_speed = 1.5  # Reduced for smoother movement
        self.ai_agent_hit_count = 0  # Resetting the hit count to 0
        self.burst_count = 0  # How many shots fired in the current burst
        self.burst_size = 30  # Fire 30 shots at a time
        self.burst_cooldown = 5000  # Pause of 5 seconds
        self.last_burst = pygame.time.get_ticks()  # When was the last time we started a burst?
        self.is_paused = False  # Is the AI paused?
        self.pause_start_time = 0  # When did the pause start?
        self.ai_hit_pause = False  # Flag to control pause
        self.ai_pause_start_time = 0  # Time the AI pause started
        self.lives_announced = [False, False, False, False]
        self.is_alive = True  # For Ai agent to not getting disappeared when hits first time
        self.x = float(x)
        self.alien_group = alien_group

    def predict_spaceship_position(self):
        # Very basic prediction - move towards where spaceship *will* be
        # based on its *current* direction.  More sophisticated solutions exist
        spaceship_x = ai_spaceship.rect.centerx
        speed = 8  # Spaceship speed

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            spaceship_x -= speed
        if keys[pygame.K_RIGHT]:
            spaceship_x += speed
        spaceship_x = max(0, min(spaceship_x, screen_width))  # clamp

        return spaceship_x

    def update(self):
         if not self.is_alive:
            return  # If the ai agent is not alive, do nothing

        # Burst fire logic
         time_now = pygame.time.get_ticks()

        # Move to predicted spaceship position.
         if ai_spaceship.alive():
            target_x = self.predict_spaceship_position()
            if self.rect.centerx < target_x:
                self.x += self.movement_speed  # small movement
            elif self.rect.centerx > target_x:
                self.x -= self.movement_speed  # small movement
            self.rect.x = int(self.x)
            self.attack()  # Call attack while moving

         if self.is_paused:
            if time_now - self.pause_start_time > self.burst_cooldown:  # 5 second pause
                self.is_paused = False
                self.last_burst = time_now  # Reset the burst timer
         else:
            if time_now - self.last_burst > 0:
                if self.burst_count < self.burst_size:
                    if time_now - self.last_shot > self.cooldown:  # Can we fire a shot?
                        # Increase the speed of bullet with level
                        speed_multiplier = 1.0 + (level * 0.05)  # 5% increase in speed per level
                        bullet = Alien_Bullets2(self.rect.centerx, self.rect.bottom, level, ai_spaceship, speed_multiplier)
                        alien_bullet_group.add(bullet)
                        self.last_shot = time_now
                        self.burst_count += 1  # increment shot count
                else:  # Burst is complete, reset
                    self.burst_count = 0  # reset the shot count
                    self.is_paused = True
                    self.pause_start_time = time_now

    def hit(self):  # Call this when ai agent is hit
        self.is_alive = False
        remaining_lives = 5 - self.ai_agent_hit_count
        if remaining_lives == 4 and not self.lives_announced[0]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[0] = True
        elif remaining_lives == 3 and not self.lives_announced[1]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[1] = True
        elif remaining_lives == 2 and not self.lives_announced[2]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[2] = True
        elif remaining_lives == 1 and not self.lives_announced[3]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[3] = True
        self.kill() # Make the AI agent disappear
        return

    def attack(self):  # Function for the ai agent to start attacking
        time_now = pygame.time.get_ticks()
        if not self.is_paused and self.is_alive:  # Make sure agent is alive
            if time_now - self.last_burst > 0:
                if self.burst_count < self.burst_size:
                    if time_now - self.last_shot > self.cooldown:  # Can we fire a shot?
                        # Increase the speed of bullet with level
                        speed_multiplier = 1.0 + (level * 0.05)  # 5% increase in speed per level
                        bullet = Alien_Bullets2(self.rect.centerx, self.rect.bottom, level, ai_spaceship, speed_multiplier)
                        alien_bullet_group.add(bullet)
                        self.last_shot = time_now
                        self.burst_count += 1  # increment shot count
                else:  # Burst is complete, reset
                    self.burst_count = 0  # reset the shot count
                    self.is_paused = True
                    self.pause_start_time = time_now

# Create AISpaceship class
class AISpaceship(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("spaceship.png")  # Or a different spaceship image
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.last_shot = pygame.time.get_ticks()
        self.cooldown = 500  # milliseconds
        self.speed = 1.75 #Reduced AI ship Speed for Smoother Movement
        self.health_start = 3 #reset the health to health start
        self.health_remaining = 3
        self.lives = 3 #Total lives of the AI SPaceship
        self.lives_announced = [False, False, False]
        self.is_alive = True  # To ensure the spaceship is active
        self.x = float(x) # For X Smoothing
        self.y = float(y) # For y Smoothing
        self.move_direction = random.choice([-1, 1])  # Initial movement direction

    def update(self):
        if not self.is_alive:
            return  # If the spaceship is not alive, do nothing

        time_now = pygame.time.get_ticks()
        # Basic movement
        self.x += self.speed * self.move_direction
        self.rect.x = int(self.x)

        if time_now - self.last_shot > self.cooldown:
            laser_fx.play()
            bullet = Bullets(self.rect.centerx, self.rect.top)
            bullet_group.add(bullet)
            self.last_shot = time_now

        # Keep within screen bounds (Horizontal)
        if self.rect.left < 0:
            self.move_direction = 1
            self.x = 0
        if self.rect.right > screen_width:
            self.move_direction = -1
            self.x = float(screen_width - self.rect.width)

    def hit(self): #Taking the damage
        if not self.is_alive:
            return
        self.health_remaining -= 1
        if self.lives > 0:  # Here to not get negative life count at the end
            if self.lives == 3 and not self.lives_announced[0]:
                self.lives -= 1
                engine.say(f"Spaceship hit! Remaining lives: {self.lives}")
                engine.runAndWait()
                self.lives_announced[0] = True

            elif self.lives == 2 and not self.lives_announced[1]:
                self.lives -= 1
                engine.say(f"Spaceship hit! Remaining lives: {self.lives}")
                engine.runAndWait()
                self.lives_announced[1] = True

            elif self.lives == 1 and not self.lives_announced[2]:
                self.lives -= 1
                engine.say(f"Spaceship hit! Remaining lives: {self.lives}")
                engine.runAndWait()
                self.lives_announced[2] = True

        if self.health_remaining <= 0 and self.lives > 0:
            explosion = Explosion(self.rect.centerx, self.rect.centery, 3)
            explosion_group.add(explosion)
            self.health_remaining = self.health_start  # reset health

        elif self.lives <= 0:  # Out of lives so game over
            explosion = Explosion(self.rect.centerx, self.rect.centery, 3)
            explosion_group.add(explosion)
            self.kill()  # Remove spaceship
            global player_won, game_over
            player_won = False  # AI lost, so player won
            game_over = True
            self.is_alive = False  # To stop calling the functions when destroyed
        return game_over


# Function to create AI Agent
def create_ai_agent2():
    global ai_agent
    ai_agent = AIAgent2(screen_width // 2, 100 + 2 * 70)  # 3rd Row
    ai_agent_group.add(ai_agent)

def create_aliens2():
    alien_group.empty()
    # Increase the number of rows and columns based on the level
    num_rows = level + 3  # Increased number of rows
    num_cols = level + 4  # Increased number of columns

    for row in range(num_rows):
        for col in range(num_cols):
            alien = Aliens2(100 + col * 80, 100 + row * 60)  # adjusted x and y coordinates
            alien_group.add(alien)

#Mode 3
# Human vs AI

class Ai_Aliens3(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("alien" + str(random.randint(1, 5)) + ".png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.move_counter = 0
        self.move_direction = 1
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 75:
            self.move_direction *= -1
            self.move_counter *= self.move_direction

        time_now = pygame.time.get_ticks()

        # Limit the number of alien bullets. Check bullet count BEFORE firing
        global alien_bullet_group
        if len(alien_bullet_group) < max_alien_bullets:  # Only fire is total bullets on screen < max
            if time_now - self.last_shot > random.randint(1000, 3000) - (level * 50):  # Firing rate increases
                bullet = Alien_Bullets3(self.rect.centerx, self.rect.bottom, level,
                                       ai_spaceship)  # Pass level to Alien_Bullets and spaceship
                alien_bullet_group.add(bullet)
                self.last_shot = time_now

# AI Defender Class
class AIDefender3(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("ai (1).jpg")  # Use a different alien image
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.last_shot = pygame.time.get_ticks()
        self.cooldown = 375  # 0.25 times faster than the aliens (500 * 0.75)
        self.movement_speed = 4  # Normal speed
        self.ai_defender_hit_count = 0  # Resetting the hit count to 0
        self.burst_count = 0  # How many shots fired in the current burst
        self.burst_size = 30  # Fire 30 shots at a time
        self.burst_cooldown = 5000  # Pause of 5 seconds
        self.last_burst = pygame.time.get_ticks()  # When was the last time we started a burst?
        self.is_paused = False  # Is the AI paused?
        self.pause_start_time = 0  # When did the pause start?
        self.ai_hit_pause = False  # Flag to control pause
        self.ai_pause_start_time = 0  # Time the AI pause started
        self.lives_announced = [False, False, False, False]

    def predict_spaceship_position(self):
        # Very basic prediction - move towards where spaceship *will* be
        # based on its *current* direction.  More sophisticated solutions exist
        spaceship_x = ai_spaceship.rect.centerx
        speed = 8  # Spaceship speed
        spaceship_x = max(screen_width//2, min(spaceship_x, screen_width))  # clamp

        return spaceship_x

    def update(self):

        # Burst fire logic
        time_now = pygame.time.get_ticks()

        # Move to predicted spaceship position.
        if ai_spaceship.alive():
            target_x = self.predict_spaceship_position()
            if self.rect.centerx < target_x:
                self.rect.x += self.movement_speed
                self.attack()  # Call attack while moving
            elif self.rect.centerx > target_x:
                self.rect.x -= self.movement_speed
                self.attack()  # Call attack while moving

        if self.is_paused:
            if time_now - self.pause_start_time > self.burst_cooldown:  # 5 second pause
                self.is_paused = False
                self.last_burst = time_now  # Reset the burst timer
        else:
            if time_now - self.last_burst > 0:
                if self.burst_count < self.burst_size:
                    if time_now - self.last_shot > self.cooldown:  # Can we fire a shot?
                        # Increase the speed of bullet with level
                        speed_multiplier = 1.0 + (level * 0.05)  # 5% increase in speed per level
                        bullet = Alien_Bullets3(self.rect.centerx, self.rect.bottom, level, ai_spaceship,
                                               speed_multiplier)
                        alien_bullet_group.add(bullet)
                        self.last_shot = time_now
                        self.burst_count += 1  # increment shot count
                else:  # Burst is complete, reset
                    self.burst_count = 0  # reset the shot count
                    self.is_paused = True
                    self.pause_start_time = time_now

    def hit(self):  # Call this when ai agent is hit
        remaining_lives = 5 - self.ai_defender_hit_count
        if remaining_lives == 4 and not self.lives_announced[0]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[0] = True
        elif remaining_lives == 3 and not self.lives_announced[1]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[1] = True
        elif remaining_lives == 2 and not self.lives_announced[2]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[2] = True
        elif remaining_lives == 1 and not self.lives_announced[3]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[3] = True

    def attack(self):  # Function for the ai agent to start attacking
        time_now = pygame.time.get_ticks()
        if not self.is_paused:  # If it is paused, don't attack
            if time_now - self.last_burst > 0:
                if self.burst_count < self.burst_size:
                    if time_now - self.last_shot > self.cooldown:  # Can we fire a shot?
                        # Increase the speed of bullet with level
                        speed_multiplier = 1.0 + (level * 0.05)  # 5% increase in speed per level
                        bullet = Alien_Bullets3(self.rect.centerx, self.rect.bottom, level, ai_spaceship,
                                               speed_multiplier)
                        alien_bullet_group.add(bullet)
                        self.last_shot = time_now
                        self.burst_count += 1  # increment shot count
                else:  # Burst is complete, reset
                    self.burst_count = 0  # reset the shot count
                    self.is_paused = True
                    self.pause_start_time = time_now

def create_ai_aliens3(level, screen_width, ai_alien_group):
    ai_alien_group.empty()
    # Increase the number of rows and columns based on the level
    num_rows = level + 3  # Increased number of rows
    num_cols = level + 4  # Increased number of columns

    for row in range(num_rows):
        for col in range(num_cols):
            alien = Ai_Aliens3(screen_width//2 + 50 + col * 60, 100 + row * 50)  # adjusted x and y coordinates

            ai_alien_group.add(alien)

# Function to create AI Agent
def create_ai_defender3():
    global ai_defender
    ai_defender = AIDefender3(screen_width // 4 * 3 , 100 + 2 * 70)  # Position on AI side
    ai_defender_group.add(ai_defender)

class Spaceship3(pygame.sprite.Sprite):
    def __init__(self, x, y, health, is_human=True):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("spaceship.png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.health_start = health
        self.health_remaining = health
        self.last_shot = pygame.time.get_ticks()
        self.lives = 3  # Initialize lives here
        self.hit_time = 0  # Time when spaceship was last hit
        self.lives_announced = [False, False, False]  # Track lives announcement
        self.is_human = is_human
        self.ai_move_direction = 1
        self.ai_last_shot = pygame.time.get_ticks()
        self.ai_fire = False


    def update(self, screen_width):
        speed = 8
        cooldown = 500  # milliseconds
        global game_over  # Use the global game_over variable
        global ai_fire

        # Apply hit pause of 1 second
        if pygame.time.get_ticks() - self.hit_time < 1000:  # 1 sec = 1000 ms
            return  # Skip movement if hit

        key = pygame.key.get_pressed()
        if self.is_human:  #Human Controlled

            if key[pygame.K_LEFT] and self.rect.left > 0:
                self.rect.x -= speed
            if key[pygame.K_RIGHT] and self.rect.right < screen_width // 2:  # Keep within left side
                self.rect.x += speed

            time_now = pygame.time.get_ticks()
            if key[pygame.K_SPACE] and time_now - self.last_shot > cooldown:
                laser_fx.play()
                bullet = Bullets3(self.rect.centerx, self.rect.top)
                bullet_group.add(bullet)
                self.last_shot = time_now
        else:   # AI Controlled
             time_now = pygame.time.get_ticks()

             # Basic AI movement (Horizontal)
             self.rect.x += self.ai_move_direction * 2  # Smaller movement speed for AI
             if self.rect.left < screen_width // 2 or self.rect.right > screen_width:
                 self.ai_move_direction *= -1  # Reverse direction at edges

             if time_now - self.last_shot > cooldown and ai_fire:  # added cooldown
                 laser_fx.play()
                 bullet = Bullets3(self.rect.centerx, self.rect.top, is_ai=True)
                 bullet_group.add(bullet)
                 self.last_shot = time_now


        self.mask = pygame.mask.from_surface(self.image)

        pygame.draw.rect(screen, red, (self.rect.x, self.rect.bottom + 10, self.rect.width, 15))
        if self.health_remaining > 0:
            pygame.draw.rect(screen, green, (
                self.rect.x, self.rect.bottom + 10, int(self.rect.width * (self.health_remaining / self.health_start)),
                15))
        else:
            explosion = Explosion(self.rect.centerx, self.rect.centery, 3)
            explosion_group.add(explosion)
            self.kill()
            if self.is_human:
                player_won = False
            else:
                ai_won = False # AI Lost
        return game_over

    def hit(self):  # Call this when player is hit
        self.hit_time = pygame.time.get_ticks()  # Mark current time

        if self.lives == 3 and not self.lives_announced[0]:
            self.lives -= 1
            engine.say(f"Spaceship hit! Remaining lives: {self.lives}")
            engine.runAndWait()
            self.lives_announced[0] = True

        elif self.lives == 2 and not self.lives_announced[1]:
            self.lives -= 1
            engine.say(f"Spaceship hit! Remaining lives: {self.lives}")
            engine.runAndWait()
            self.lives_announced[1] = True

        elif self.lives == 1 and not self.lives_announced[2]:
            self.lives -= 1
            engine.say(f"Spaceship hit! Remaining lives: {self.lives}")
            engine.runAndWait()
            self.lives_announced[2] = True
        elif self.lives == 0:
            global game_over
            game_over = True

class Bullets3(pygame.sprite.Sprite):
    def __init__(self, x, y, is_ai=False):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("bullet.png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.is_ai = is_ai  #Track AI Bullets

    def update(self):
        if not self.is_ai:
            self.rect.y -= 5
        else:
            self.rect.y -= 5  # Adjusted bullet speed for AI bullets

        if self.rect.bottom < 0:
            self.kill()

        # Check if bullet hits the AI Agent
        global ai_agent, score, player_won, game_over
        if ai_agent and pygame.sprite.spritecollide(self, ai_agent_group, False):
            self.kill()
            explosion_fx.play()
            explosion = Explosion(self.rect.centerx, self.rect.centery, 2)
            explosion_group.add(explosion)
            score -= 20  # Decrease player's score

            ai_agent.ai_agent_hit_count += 1
            remaining_lives = 5 - ai_agent.ai_agent_hit_count

            if remaining_lives >= 0:
                if remaining_lives == 4 and not ai_agent.lives_announced[0]:
                    engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
                    engine.runAndWait()
                    ai_agent.lives_announced[0] = True
                elif remaining_lives == 3 and not ai_agent.lives_announced[1]:
                    engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
                    engine.runAndWait()
                    ai_agent.lives_announced[1] = True
                elif remaining_lives == 2 and not ai_agent.lives_announced[2]:
                    engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
                    engine.runAndWait()
                    ai_agent.lives_announced[2] = True
                elif remaining_lives == 1 and not ai_agent.lives_announced[3]:
                    engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
                    engine.runAndWait()
                    ai_agent.lives_announced[3] = True

            if ai_agent.ai_agent_hit_count >= 5:
                ai_agent.kill()
                ai_agent = None
                explosion2_fx.play()

        # Update score when hitting an alien
        elif not self.is_ai and pygame.sprite.spritecollide(self, alien_group, True): #Human
            self.kill()
            explosion_fx.play()
            explosion = Explosion(self.rect.centerx, self.rect.centery, 2)
            explosion_group.add(explosion)
            score += 10  # Increase score by 10

            global human_level_end_time
            if len(alien_group) == 0 and human_level_end_time == 0:
                human_level_end_time = pygame.time.get_ticks()

        elif self.is_ai and pygame.sprite.spritecollide(self, ai_alien_group, True):  # For the AI Side
            self.kill()
            explosion_fx.play()
            explosion = Explosion(self.rect.centerx, self.rect.centery, 2)
            explosion_group.add(explosion)
            global ai_level_end_time
            if len(ai_alien_group) == 0 and ai_level_end_time == 0:
                ai_level_end_time = pygame.time.get_ticks()

class Aliens3(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("alien" + str(random.randint(1, 5)) + ".png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.move_counter = 0
        self.move_direction = 1
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 75:
            self.move_direction *= -1
            self.move_counter *= self.move_direction

        time_now = pygame.time.get_ticks()

        # Limit the number of alien bullets. Check bullet count BEFORE firing
        global alien_bullet_group
        if len(alien_bullet_group) < max_alien_bullets:  # Only fire is total bullets on screen < max
            if time_now - self.last_shot > random.randint(1000, 3000) - (level * 50):  # Firing rate increases
                bullet = Alien_Bullets3(self.rect.centerx, self.rect.bottom, level,
                                       human_spaceship)  # Pass level to Alien_Bullets and spaceship
                alien_bullet_group.add(bullet)
                self.last_shot = time_now

class Alien_Bullets3(pygame.sprite.Sprite):
    def __init__(self, x, y, level, spaceship, speed_multiplier=1.0):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("alien_bullet.png")
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.base_speed = 1.5 + (level * 0.3)  # Base speed + level scaling
        self.speed = self.base_speed * speed_multiplier  # Apply speed multiplier
        self.spaceship = spaceship  # Store the spaceship object

    def update(self, spaceship_group, ai_spaceship_group):
        self.rect.y += self.speed
        if self.rect.top > screen_height:
            self.kill()

        #Checking which side for bullet is to collide with spaceship
        if self.spaceship.is_human:

            if pygame.sprite.spritecollide(self, spaceship_group, False, pygame.sprite.collide_mask):
                self.kill()
                explosion2_fx.play()
                self.spaceship.health_remaining -= 1  # Update lives of spaceship object and not of class
                self.spaceship.hit()  # Call to mark the player as hit
                explosion = Explosion(self.rect.centerx, self.rect.centery, 1)
                explosion_group.add(explosion)

        else:
            if pygame.sprite.spritecollide(self, ai_spaceship_group, False, pygame.sprite.collide_mask):
                self.kill()
                explosion2_fx.play()
                self.spaceship.health_remaining -= 1  # Update lives of spaceship object and not of class
                self.spaceship.hit()  # Call to mark the player as hit
                explosion = Explosion(self.rect.centerx, self.rect.centery, 1)
                explosion_group.add(explosion)

# AI Agent Class
class AIAgent3(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("ai (1).jpg")  # Use a different alien image
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.last_shot = pygame.time.get_ticks()
        self.cooldown = 375  # 0.25 times faster than the aliens (500 * 0.75)
        self.movement_speed = 4  # Normal speed
        self.ai_agent_hit_count = 0  # Resetting the hit count to 0
        self.burst_count = 0  # How many shots fired in the current burst
        self.burst_size = 30  # Fire 30 shots at a time
        self.burst_cooldown = 5000  # Pause of 5 seconds
        self.last_burst = pygame.time.get_ticks()  # When was the last time we started a burst?
        self.is_paused = False  # Is the AI paused?
        self.pause_start_time = 0  # When did the pause start?
        self.ai_hit_pause = False  # Flag to control pause
        self.ai_pause_start_time = 0  # Time the AI pause started
        self.lives_announced = [False, False, False, False]

    def predict_spaceship_position(self, human_spaceship, screen_width):
        # Very basic prediction - move towards where spaceship *will* be
        # based on its *current* direction.  More sophisticated solutions exist
        spaceship_x = human_spaceship.rect.centerx
        speed = 8  # Spaceship speed

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            spaceship_x -= speed
        if keys[pygame.K_RIGHT]:
            spaceship_x += speed
        spaceship_x = max(0, min(spaceship_x, screen_width // 2))  # clamp

        return spaceship_x

    def update(self, human_spaceship, screen_width):

        # Burst fire logic
        time_now = pygame.time.get_ticks()

        # Move to predicted spaceship position.
        if human_spaceship.alive():
            target_x = self.predict_spaceship_position(human_spaceship, screen_width)
            if self.rect.centerx < target_x:
                self.rect.x += self.movement_speed
                self.attack(human_spaceship, level)  # Call attack while moving
            elif self.rect.centerx > target_x:
                self.rect.x -= self.movement_speed
                self.attack(human_spaceship, level)  # Call attack while moving

        if self.is_paused:
            if time_now - self.pause_start_time > self.burst_cooldown:  # 5 second pause
                self.is_paused = False
                self.last_burst = time_now  # Reset the burst timer
        else:
            if time_now - self.last_burst > 0:
                if self.burst_count < self.burst_size:
                    if time_now - self.last_shot > self.cooldown:  # Can we fire a shot?
                        # Increase the speed of bullet with level
                        speed_multiplier = 1.0 + (level * 0.05)  # 5% increase in speed per level
                        bullet = Alien_Bullets3(self.rect.centerx, self.rect.bottom, level, human_spaceship,
                                               speed_multiplier)
                        alien_bullet_group.add(bullet)
                        self.last_shot = time_now
                        self.burst_count += 1  # increment shot count
                else:  # Burst is complete, reset
                    self.burst_count = 0  # reset the shot count
                    self.is_paused = True
                    self.pause_start_time = time_now

    def hit(self):  # Call this when ai agent is hit
        remaining_lives = 5 - self.ai_agent_hit_count
        if remaining_lives == 4 and not self.lives_announced[0]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[0] = True
        elif remaining_lives == 3 and not self.lives_announced[1]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[1] = True
        elif remaining_lives == 2 and not self.lives_announced[2]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[2] = True
        elif remaining_lives == 1 and not self.lives_announced[3]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[3] = True

    def attack(self, human_spaceship, level):  # Function for the ai agent to start attacking
        time_now = pygame.time.get_ticks()
        if not self.is_paused:  # If it is paused, don't attack
            if time_now - self.last_burst > 0:
                if self.burst_count < self.burst_size:
                    if time_now - self.last_shot > self.cooldown:  # Can we fire a shot?
                        # Increase the speed of bullet with level
                        speed_multiplier = 1.0 + (level * 0.05)  # 5% increase in speed per level
                        bullet = Alien_Bullets3(self.rect.centerx, self.rect.bottom, level, human_spaceship,
                                               speed_multiplier)
                        alien_bullet_group.add(bullet)
                        self.last_shot = time_now
                        self.burst_count += 1  # increment shot count
                else:  # Burst is complete, reset
                    self.burst_count = 0  # reset the shot count
                    self.is_paused = True
                    self.pause_start_time = time_now

# AI Defender Class
class AIDefender3(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("ai (1).jpg")  # Use a different alien image
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.last_shot = pygame.time.get_ticks()
        self.cooldown = 375  # 0.25 times faster than the aliens (500 * 0.75)
        self.movement_speed = 4  # Normal speed
        self.ai_defender_hit_count = 0  # Resetting the hit count to 0
        self.burst_count = 0  # How many shots fired in the current burst
        self.burst_size = 30  # Fire 30 shots at a time
        self.burst_cooldown = 5000  # Pause of 5 seconds
        self.last_burst = pygame.time.get_ticks()  # When was the last time we started a burst?
        self.is_paused = False  # Is the AI paused?
        self.pause_start_time = 0  # When did the pause start?
        self.ai_hit_pause = False  # Flag to control pause
        self.ai_pause_start_time = 0  # Time the AI pause started
        self.lives_announced = [False, False, False, False]

    def predict_spaceship_position(self):
        # Very basic prediction - move towards where spaceship *will* be
        # based on its *current* direction.  More sophisticated solutions exist
        spaceship_x = ai_spaceship.rect.centerx
        speed = 8  # Spaceship speed
        spaceship_x = max(screen_width//2, min(spaceship_x, screen_width))  # clamp

        return spaceship_x

    def update(self):

        # Burst fire logic
        time_now = pygame.time.get_ticks()

        # Move to predicted spaceship position.
        if ai_spaceship.alive():
            target_x = self.predict_spaceship_position()
            if self.rect.centerx < target_x:
                self.rect.x += self.movement_speed
                self.attack()  # Call attack while moving
            elif self.rect.centerx > target_x:
                self.rect.x -= self.movement_speed
                self.attack()  # Call attack while moving

        if self.is_paused:
            if time_now - self.pause_start_time > self.burst_cooldown:  # 5 second pause
                self.is_paused = False
                self.last_burst = time_now  # Reset the burst timer
        else:
            if time_now - self.last_burst > 0:
                if self.burst_count < self.burst_size:
                    if time_now - self.last_shot > self.cooldown:  # Can we fire a shot?
                        # Increase the speed of bullet with level
                        speed_multiplier = 1.0 + (level * 0.05)  # 5% increase in speed per level
                        bullet = Alien_Bullets3(self.rect.centerx, self.rect.bottom, level, ai_spaceship,
                                               speed_multiplier)
                        alien_bullet_group.add(bullet)
                        self.last_shot = time_now
                        self.burst_count += 1  # increment shot count
                else:  # Burst is complete, reset
                    self.burst_count = 0  # reset the shot count
                    self.is_paused = True
                    self.pause_start_time = time_now

    def hit(self):  # Call this when ai agent is hit
        remaining_lives = 5 - self.ai_defender_hit_count
        if remaining_lives == 4 and not self.lives_announced[0]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[0] = True
        elif remaining_lives == 3 and not self.lives_announced[1]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[1] = True
        elif remaining_lives == 2 and not self.lives_announced[2]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[2] = True
        elif remaining_lives == 1 and not self.lives_announced[3]:
            engine.say(f"Defender hit! Remaining lives: {remaining_lives}")
            engine.runAndWait()
            self.lives_announced[3] = True

    def attack(self):  # Function for the ai agent to start attacking
        time_now = pygame.time.get_ticks()
        if not self.is_paused:  # If it is paused, don't attack
            if time_now - self.last_burst > 0:
                if self.burst_count < self.burst_size:
                    if time_now - self.last_shot > self.cooldown:  # Can we fire a shot?
                        # Increase the speed of bullet with level
                        speed_multiplier = 1.0 + (level * 0.05)  # 5% increase in speed per level
                        bullet = Alien_Bullets3(self.rect.centerx, self.rect.bottom, level, ai_spaceship,
                                               speed_multiplier)
                        alien_bullet_group.add(bullet)
                        self.last_shot = time_now
                        self.burst_count += 1  # increment shot count
                else:  # Burst is complete, reset
                    self.burst_count = 0  # reset the shot count
                    self.is_paused = True
                    self.pause_start_time = time_now

def create_ai_aliens3(level, screen_width, ai_alien_group):
    ai_alien_group.empty()
    # Increase the number of rows and columns based on the level
    num_rows = level + 3  # Increased number of rows
    num_cols = level + 4  # Increased number of columns

    for row in range(num_rows):
        for col in range(num_cols):
            alien = Ai_Aliens3(screen_width//2 + 50 + col * 60, 100 + row * 50)  # adjusted x and y coordinates

            ai_alien_group.add(alien)

# Function to create AI Agent
def create_ai_defender3():
    global ai_defender
    ai_defender = AIDefender3(screen_width // 4 * 3 , 100 + 2 * 70)  # Position on AI side
    ai_defender_group.add(ai_defender)

# --- New Variables for Mode 3 ---
human_wins = 0
ai_wins = 0
level_winner = None  # 'human', 'ai', or None
human_level_end_time = 0
ai_level_end_time = 0
level_start_time = 0  # Common level start time
max_levels = 3
ai_won = False
score = 0
ai_fire = False
winner_announced = False

def draw_bg3(mode3, screen_width):
    screen.blit(bg, (0, 0))
    if mode3:
        screen.blit(bg, (screen_width // 2, 0))  # Draw background for AI side
    # Draw win counts at the top
    draw_text(f"Human Wins: {human_wins}", font30, white, 10, 10)
    draw_text(f"AI Wins: {ai_wins}", font30, white, screen_width - 200, 10)

def create_aliens3(level, screen_width, alien_group):
    alien_group.empty()
    # Increase the number of rows and columns based on the level
    num_rows = level + 3  # Increased number of rows
    num_cols = level + 4  # Increased number of columns

    for row in range(num_rows):
        for col in range(num_cols):
            alien = Aliens3(50 + col * 60, 100 + row * 50)  # adjusted x and y coordinates

            alien_group.add(alien)

# Function to create AI Agent
def create_ai_agent3(screen_width, ai_agent_group, human_spaceship):
    global ai_agent
    ai_agent = AIAgent3(screen_width // 4, 100 + 2 * 70)  # Position on human side
    ai_agent_group.add(ai_agent)

def reset_ai_agent3():  # Creating reset function
    global ai_agent
    if ai_agent:
        ai_agent.kill()  # remove the ai agent
    ai_agent = None  # set it to none so as to reset all properties

def reset_ai_defender3():
    global ai_defender
    if ai_defender:
        ai_defender.kill()
    ai_defender = None

def draw_menu():
    screen.fill(black)
    draw_text("Space Invaders", font60, white, screen_width // 2 - 200, screen_height // 4)
    draw_text("1. The Defender Strike", font40, white, screen_width // 2 - 180, screen_height // 2 - 50)
    draw_text("2. AI VS Defender", font40, white, screen_width // 2 - 180, screen_height // 2 + 20)
    draw_text("3. Human vs AI", font40, white, screen_width // 2 - 180, screen_height // 2 + 90)
    draw_text("4. Exit", font40, white, screen_width // 2 - 180, screen_height // 2 + 160)
    draw_text("Press the corresponding number to choose a mode.", font18, grey, screen_width // 2 - 200, screen_height // 2 + 230)
    pygame.display.update()

# Game loop
run = True
game_mode = 0
menu = True

human_spaceship = None
ai_spaceship = None
spaceship_group = None
ai_spaceship_group = None
bullet_group = None
alien_group = None
ai_alien_group = None
alien_bullet_group = None
explosion_group = None
ai_agent_group = None
ai_defender_group = None

level = 1
max_levels = 5
ai_agent = None
ai_defender = None
max_alien_bullets = 5
game_over = False
player_won = False
ai_won = False
score = 0
last_hit = 0
start_time = 0
level_start_time = 0
display_level_timer = 0
display_level_duration = 3
display_level = True
get_ready_time = 3
start_time = 0
game_started = False
countdown_number = 3
game_start_time = 0
game_end_time = 0
human_level_end_time = 0
ai_level_end_time = 0
winner_announced = False
ai_fire = False


while run:
    clock.tick(fps)

    if menu:
        draw_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    game_mode = 1
                    menu = False
                    # Reset variables
                    screen_width = 600
                    screen = pygame.display.set_mode((screen_width, screen_height))
                    level = 1
                    max_levels = 5
                    ai_agent = None
                    max_alien_bullets = 5
                    game_over = False
                    player_won = False
                    score = 0
                    last_hit = 0
                    start_time = 0
                    level_start_time = 0
                    display_level_timer = 0
                    display_level_duration = 3
                    display_level = True
                    get_ready_time = 3
                    start_time = 0
                    game_started = False
                    countdown_number = 3
                    game_start_time = 0
                    game_end_time = 0
                    winner_announced = False
                    ai_fire = False
                    # Initialize Sprite Groups
                    spaceship_group = pygame.sprite.Group()
                    bullet_group = pygame.sprite.Group()
                    alien_group = pygame.sprite.Group()
                    alien_bullet_group = pygame.sprite.Group()
                    explosion_group = pygame.sprite.Group()
                    ai_agent_group = pygame.sprite.Group()

                    # Initialize Spaceship
                    spaceship = Spaceship(int(screen_width / 2), screen_height - 100, 3)
                    spaceship_group.add(spaceship)

                    create_aliens()
                    start_time = pygame.time.get_ticks()

                elif event.key == pygame.K_2:
                    game_mode = 2
                    menu = False
                    # Reset variables
                    screen_width = 600
                    screen = pygame.display.set_mode((screen_width, screen_height))
                    level = 1
                    max_levels = 5
                    ai_agent = None
                    max_alien_bullets = 5
                    game_over = False
                    player_won = False
                    score = 0
                    last_hit = 0
                    start_time = 0
                    level_start_time = 0
                    display_level_timer = 0
                    display_level_duration = 3
                    display_level = True
                    get_ready_time = 3
                    start_time = 0
                    game_started = False
                    countdown_number = 3
                    game_start_time = 0
                    game_end_time = 0
                    winner_announced = False
                    ai_fire = False
                    # Initialize Sprite Groups
                    spaceship_group = pygame.sprite.Group()
                    bullet_group = pygame.sprite.Group()
                    alien_group = pygame.sprite.Group()
                    alien_bullet_group = pygame.sprite.Group()
                    explosion_group = pygame.sprite.Group()
                    ai_agent_group = pygame.sprite.Group()
                    ai_spaceship_group = pygame.sprite.Group()

                    # Initialize AISpaceship

                    ai_spaceship = AISpaceship(int(screen_width / 2), screen_height - 100)
                    ai_spaceship_group.add(ai_spaceship)

                    create_aliens2()
                    start_time = pygame.time.get_ticks()

                elif event.key == pygame.K_3:
                    game_mode = 3
                    menu = False
                    # Reset variables
                    screen_width = 1200
                    screen = pygame.display.set_mode((screen_width, screen_height))
                    level = 1
                    max_levels = 3
                    ai_agent = None
                    max_alien_bullets = 5
                    game_over = False
                    player_won = False
                    ai_won = False
                    score = 0
                    last_hit = 0
                    start_time = 0
                    level_start_time = 0
                    display_level_timer = 0
                    display_level_duration = 3
                    display_level = True
                    get_ready_time = 3
                    start_time = 0
                    game_started = False
                    countdown_number = 3
                    game_start_time = 0
                    game_end_time = 0
                    human_level_end_time = 0
                    ai_level_end_time = 0
                    winner_announced = False
                    ai_fire = False
                    human_wins = 0
                    ai_wins = 0

                    # Initialize Sprite Groups
                    spaceship_group = pygame.sprite.Group()
                    ai_spaceship_group = pygame.sprite.Group()
                    bullet_group = pygame.sprite.Group()
                    alien_group = pygame.sprite.Group()
                    ai_alien_group = pygame.sprite.Group()
                    alien_bullet_group = pygame.sprite.Group()
                    explosion_group = pygame.sprite.Group()
                    ai_agent_group = pygame.sprite.Group()
                    ai_defender_group = pygame.sprite.Group()

                    # Initialize Spaceships
                    human_spaceship = Spaceship3(int(screen_width / 4), screen_height - 100, 3, is_human=True)
                    ai_spaceship = Spaceship3(int(screen_width * 3 / 4), screen_height - 100, 3, is_human=False)
                    spaceship_group.add(human_spaceship)
                    ai_spaceship_group.add(ai_spaceship)

                    create_aliens3(level, screen_width, alien_group)
                    create_ai_aliens3(level, screen_width, ai_alien_group)
                    start_time = pygame.time.get_ticks()

                elif event.key == pygame.K_4:
                    run = False

    else:
        if game_mode == 1:
            draw_bg()

            # Display level at the start
            if display_level:
                time_now = pygame.time.get_ticks()
                if (time_now - level_start_time) < (display_level_duration * 1000):
                    level_text = font60.render(f'Level {level}', True, white)
                    level_rect = level_text.get_rect(center=(screen_width // 2, screen_height // 2))
                    screen.blit(level_text, level_rect)
                    if not level_announced:
                        engine.say(f"Entering Level {level} {player_name}!")
                        engine.runAndWait()
                        level_announced = True

                else:
                    display_level = False
                    game_start_time = pygame.time.get_ticks()  # Game actually begins now

            # Get Ready Timer Logic
            elif not game_started and not game_over:
                current_time = pygame.time.get_ticks()
                time_elapsed = (current_time - start_time) / 1000
                if time_elapsed < get_ready_time:
                    countdown_number = int(get_ready_time - time_elapsed)
                    if countdown_number > 0:
                        draw_text(str(countdown_number), font40, white, screen_width // 2 - 10, screen_height // 2 - 50)
                    else:
                        draw_text("Go!", font40, white, screen_width // 2 - 30, screen_height // 2 - 50)
                        engine.say(f"Go {player_name}!")
                        engine.runAndWait()
                else:
                    game_started = True
                    game_start_time = pygame.time.get_ticks()  # Set game start time

            elif game_over:
                draw_text("Game Over", font40, white, screen_width // 2 - 100, screen_height // 2 - 50)  # Draw game over text
                if not game_over_announced:
                    engine.say(f"Game Over {player_name}!")
                    engine.runAndWait()
                    game_over_announced = True  # set game over annouced to true
                if player_won:
                    draw_text("You Win!", font40, white, screen_width // 2 - 100, screen_height // 2 + 50)
                    engine.say(f"{player_name} You Win!")
                    engine.runAndWait()

                # Calculate final time
                total_time_seconds = (game_end_time - game_start_time) / 1000
                minutes = int(total_time_seconds // 60)
                seconds = int(total_time_seconds % 60)
                time_string = f"Time: {minutes:02}:{seconds:02}"  # format time
                draw_text(time_string, font30, white, screen_width // 2 - 50, screen_height // 2 + 100)

                # Display the final score
                score_text = f"Score: {score}"
                draw_text(score_text, font30, white, screen_width // 2 - 50, screen_height // 2 + 150)

            else:

                spaceship.update()
                bullet_group.update()
                alien_group.update()
                alien_bullet_group.update()
                explosion_group.update()
                if ai_agent:
                    ai_agent.update()
                    ai_agent_group.update()

                spaceship_group.draw(screen)
                bullet_group.draw(screen)
                alien_group.draw(screen)
                alien_bullet_group.draw(screen)
                explosion_group.draw(screen)
                if ai_agent:
                    ai_agent_group.draw(screen)

                # Calculate time elapsed only when the game is not over
                if not game_over:
                    time_elapsed = pygame.time.get_ticks() - game_start_time
                total_time_seconds = (pygame.time.get_ticks() - game_start_time) / 1000
                minutes = int(total_time_seconds // 60)
                seconds = int(total_time_seconds % 60)
                time_string = f"Time: {minutes:02}:{seconds:02}"

                # Display the time
                draw_text(time_string, font30, white, 10, 10)
                # Display the score
                score_text = f"Score: {score}"
                draw_text(score_text, font30, white, 10, 40)

                # Display the remaining lives in the top right corner
                lives_text = f"Lives: {spaceship.lives}"
                draw_text(lives_text, font30, white, screen_width - 200, 10)

                # Display game timer
                draw_text(time_string, font30, white, screen_width - 150, 40)

                if spaceship.lives <= 0:
                    game_over = True
                    game_end_time = pygame.time.get_ticks()

                if len(alien_group) == 0 and level < max_levels:
                    level += 1
                    level_announced = False
                    reset_ai_agent()
                    create_aliens()
                    level_start_time = pygame.time.get_ticks()
                    display_level = True
                    if level >= 2 and ai_agent is None:
                        create_ai_agent()
                elif len(alien_group) == 0 and level == max_levels:
                    game_over = True
                    player_won = True
                    game_end_time = pygame.time.get_ticks()
                    if player_won:
                        engine.say(f"{player_name} You Win!")
                        engine.runAndWait()
                elif level == max_levels and len(alien_group) == 0:
                    game_over = True
                    player_won = True
                    game_end_time = pygame.time.get_ticks()
                    if player_won:
                        engine.say(f"{player_name} You Win!")
                        engine.runAndWait()

        elif game_mode == 2:
            draw_bg()

            # Get Ready Timer Logic
            if not game_started and not game_over:
                current_time = pygame.time.get_ticks()
                time_elapsed = (current_time - start_time) / 1000
                if time_elapsed < get_ready_time:
                    countdown_number = int(get_ready_time - time_elapsed)
                    draw_text("Get Ready", font40, white, screen_width // 2 - 100, screen_height // 2 - 50)
                    draw_text(str(countdown_number), font60, white, screen_width // 2 - 20, screen_height // 2 + 10)
                else:
                    game_started = True
                    game_start_time = pygame.time.get_ticks()

            # Display level at the start
            elif display_level:
                time_now = pygame.time.get_ticks()
                if (time_now - level_start_time) < (display_level_duration * 1000):
                    level_text = font60.render(f'Level {level}', True, white)
                    level_rect = level_text.get_rect(center=(screen_width // 2, screen_height // 2))
                    screen.blit(level_text, level_rect)
                    if not level_announced:
                        engine.say(f"Entering Level {level}")
                        engine.runAndWait()
                        level_announced = True

                else:
                    display_level = False
                    game_start_time = pygame.time.get_ticks()

            elif game_over:
                draw_text("Game Over", font40, white, screen_width // 2 - 100, screen_height // 2 - 50)
                if not game_over_announced:
                    engine.say("Game Over!")
                    engine.runAndWait()
                    game_over_announced = True
                if player_won:
                    draw_text("Player Wins!", font40, white, screen_width // 2 - 100, screen_height // 2 + 50)
                    engine.say("Player Wins!")
                    engine.runAndWait()

                # Calculate final time
                total_time_seconds = (game_end_time - game_start_time) / 1000
                minutes = int(total_time_seconds // 60)
                seconds = int(total_time_seconds % 60)
                time_string = f"Time: {minutes:02}:{seconds:02}"
                draw_text(time_string, font30, white, screen_width // 2 - 50, screen_height // 2 + 100)

                # Display the final score
                score_text = f"Score: {score}"
                draw_text(score_text, font30, white, screen_width // 2 - 50, screen_height // 2 + 150)

            else:

                ai_spaceship.update()
                bullet_group.update()
                alien_group.update()
                alien_bullet_group.update()
                explosion_group.update()
                if ai_agent and ai_agent.is_alive:
                    ai_agent.update()


                ai_spaceship_group.draw(screen)
                spaceship_group.draw(screen)
                bullet_group.draw(screen)
                alien_group.draw(screen)
                alien_bullet_group.draw(screen)
                explosion_group.draw(screen)
                if ai_agent and ai_agent.is_alive:
                    ai_agent_group.draw(screen)

                # Calculate time elapsed only when the game is not over
                if not game_over:
                    time_elapsed = pygame.time.get_ticks() - game_start_time
                total_time_seconds = (pygame.time.get_ticks() - game_start_time) / 1000
                minutes = int(total_time_seconds // 60)
                seconds = int(total_time_seconds % 60)
                time_string = f"Time: {minutes:02}:{seconds:02}"

                # Display the time
                draw_text(time_string, font30, white, 10, 10)
                # Display the score
                score_text = f"Score: {score}"
                draw_text(score_text, font30, white, 10, 40)

                # Display the remaining lives in the top right corner
                lives_text = f"Lives: {ai_spaceship.lives}"
                draw_text(lives_text, font30, white, screen_width - 200, 10)

                # Display game timer
                draw_text(time_string, font30, white, screen_width - 150, 40)

                if ai_spaceship.lives <= 0 and not ai_spaceship.is_alive:
                    game_over = True
                    ai_spaceship.is_alive=False
                    game_end_time = pygame.time.get_ticks()

                if len(alien_group) == 0 and level < max_levels:
                    level += 1
                    level_announced = False
                    reset_ai_agent()
                    create_aliens2()
                    level_start_time = pygame.time.get_ticks()
                    display_level = True
                    if level >= 2 and ai_agent is None:
                        create_ai_agent2()
                elif len(alien_group) == 0 and level == max_levels:
                    game_over = True
                    player_won = True
                    game_end_time = pygame.time.get_ticks()
                    if player_won:
                        engine.say("Player Wins!")
                        engine.runAndWait()
                elif level == max_levels and len(alien_group) == 0:
                    game_over = True
                    player_won = True
                    game_end_time = pygame.time.get_ticks()
                    if player_won:
                        engine.say("Player Wins!")
                        engine.runAndWait()

        elif game_mode == 3:
            # Drawing line
            pygame.draw.line(screen, white, (screen_width//2, 0), (screen_width//2, screen_height), 2)
            draw_bg3(True, screen_width)

            # Display level at the start
            if display_level:
                time_now = pygame.time.get_ticks()
                if (time_now - level_start_time) < (display_level_duration * 1000):
                    level_text = font60.render(f'Level {level}', True, white)
                    level_rect = level_text.get_rect(center=(screen_width // 2, screen_height // 2))
                    screen.blit(level_text, level_rect)
                    if not level_announced:
                        engine.say(f"Entering Level {level}")
                        engine.runAndWait()
                        level_announced = True

                else:
                    display_level = False
                    game_start_time = pygame.time.get_ticks()

            # Get Ready Timer Logic
            elif not game_started and not game_over:
                current_time = pygame.time.get_ticks()
                time_elapsed = (current_time - start_time) / 1000
                if time_elapsed < get_ready_time:
                    countdown_number = int(get_ready_time - time_elapsed)
                    if countdown_number > 0:
                        draw_text(str(countdown_number), font40, white, screen_width // 2 - 10, screen_height // 2 - 50)
                    else:
                        draw_text("Go!", font40, white, screen_width // 2 - 30, screen_height // 2 - 50)
                else:
                    game_started = True
                    game_start_time = pygame.time.get_ticks()
                    ai_fire = True

            elif game_over:
                draw_text("Game Over", font40, white, screen_width // 2 - 100, screen_height // 2 - 50)
                if not game_over_announced:
                    engine.say("Game Over!")
                    engine.runAndWait()
                    game_over_announced = True

                human_wins_text = font40.render(f"Human Wins: {human_wins}", True, white)
                ai_wins_text = font40.render(f"AI Wins: {ai_wins}", True, white)
                human_wins_rect = human_wins_text.get_rect(center=(screen_width // 2, screen_height // 2 + 50))
                ai_wins_rect = ai_wins_text.get_rect(center=(screen_width // 2, screen_height // 2 + 100))
                screen.blit(human_wins_text, human_wins_rect)
                screen.blit(ai_wins_text, ai_wins_rect)

                winnerText = ""
                if human_wins > ai_wins:
                    winnerText = "Human Wins the Game!"
                elif ai_wins > human_wins:
                     winnerText = "AI Wins the Game!"
                else:
                     winnerText = "Game is a Tie!"

                draw_text(winnerText, font40, white, screen_width // 2 - 200, screen_height // 2 + 150)

                if not winner_announced:
                    engine.say(winnerText)
                    engine.runAndWait()
                    winner_announced = True

            else:

                human_spaceship.update(screen_width)
                ai_spaceship.update(screen_width)
                bullet_group.update()
                alien_group.update()
                ai_alien_group.update()

                for bullet in alien_bullet_group:
                    bullet.update(spaceship_group, ai_spaceship_group)

                explosion_group.update()
                if ai_agent:
                    ai_agent.update(human_spaceship, screen_width)
                    ai_agent_group.update(human_spaceship, screen_width)

                if ai_defender:
                    ai_defender.update()
                    ai_defender_group.update()

                spaceship_group.draw(screen)
                ai_spaceship_group.draw(screen)
                bullet_group.draw(screen)
                alien_group.draw(screen)
                ai_alien_group.draw(screen)
                alien_bullet_group.draw(screen)
                explosion_group.draw(screen)
                if ai_agent:
                    ai_agent_group.draw(screen)

                if ai_defender:
                    ai_defender_group.draw(screen)

                # Calculate time elapsed only when the game is not over
                if not game_over:
                    time_elapsed = pygame.time.get_ticks() - game_start_time
                total_time_seconds = (pygame.time.get_ticks() - game_start_time) / 1000
                minutes = int(total_time_seconds // 60)
                seconds = int(total_time_seconds % 60)
                time_string = f"Time: {minutes:02}:{seconds:02}"

                # Display the time
                draw_text(time_string, font30, white, 10, 10)
                # Display the score
                score_text = f"Score: {score}"
                draw_text(score_text, font30, white, 10, 40)

                # Display the remaining lives in the top right corner
                draw_text(f"Human Lives: {human_spaceship.lives}", font30, white, screen_width // 2 - 200, 10)
                draw_text(f"Ai Lives: {ai_spaceship.lives}", font30, white, screen_width - 200, 10)

                # Display game timer
                draw_text(time_string, font30, white, screen_width // 2 - 150, 40)

                if human_spaceship.lives <= 0 or ai_spaceship.lives <= 0:
                    game_over = True
                    game_end_time = pygame.time.get_ticks()

                if len(alien_group) == 0 or len(ai_alien_group) == 0:
                    level_winner = None
                    if human_level_end_time > 0 and ai_level_end_time > 0:
                        if human_level_end_time < ai_level_end_time:
                            level_winner = "human"
                            human_wins += 1
                        elif ai_level_end_time < human_level_end_time:
                            level_winner = "ai"
                            ai_wins += 1
                        else:
                            level_winner = "tie"
                    elif len(alien_group) == 0 and len(ai_alien_group) != 0:
                        level_winner = "human"
                        human_wins += 1
                    elif len(ai_alien_group) == 0 and len(alien_group) != 0:
                        level_winner = "ai"
                        ai_wins += 1
                    else:
                        level_winner = "tie"

                    if level_winner == "human":
                        engine.say("Human wins the level!")
                        engine.runAndWait()
                    elif level_winner == "ai":
                        engine.say("AI wins the level!")
                        engine.runAndWait()
                    else:
                        engine.say("Level Tie!")
                        engine.runAndWait()

                    if level < max_levels:
                        level += 1
                        level_announced = False
                        reset_ai_agent3()
                        reset_ai_defender3()
                        ai_fire = True

                        create_ai_aliens3(level, screen_width, ai_alien_group)
                        create_aliens3(level, screen_width, alien_group)
                        human_level_end_time = 0
                        ai_level_end_time = 0

                        level_start_time = pygame.time.get_ticks()
                        display_level = True
                        if level >= 2:
                            create_ai_agent3(screen_width, ai_agent_group, human_spaceship)
                            create_ai_defender3()

                    else:
                        game_over = True
                        game_end_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()