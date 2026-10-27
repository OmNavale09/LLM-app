# Instructions on how to play the game:
# ------------------------------------
# Title: Dino Dash
# Objective: Control a small dinosaur character, jumping over incoming cacti and pterodactyls to survive for as long as possible and achieve the highest score.
#
# Controls:
# - Press the 'SPACEBAR' or 'UP ARROW KEY' to make the dinosaur jump.
#   You cannot double jump; you must land on the ground before jumping again.
#
# Gameplay:
# - Your dinosaur runs automatically from left to right.
# - Obstacles (cacti and flying pterodactyls) will appear and scroll towards you.
# - Jump over cacti.
# - Jump over or duck under pterodactyls depending on their height.
# - The game speed and obstacle frequency will gradually increase, making it more challenging.
#
# Scoring:
# - You earn points for every second you survive.
# - Your current score is displayed at the top right of the screen.
#
# Game Over:
# - If your dinosaur collides with any obstacle, the game ends.
# - Your final score will be displayed.
# - To restart the game, press the 'R' key.
# ------------------------------------

import pygame
import sys
import random

# --- Game Initialization ---
pygame.init()

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
GROUND_HEIGHT = 50  # Height of the ground plane
DINO_HEIGHT = 60
DINO_WIDTH = 40

# Colors
WHITE = (255, 255, 255)  # Background color (desert sky)
BLACK = (0, 0, 0)      # Color for cacti and text
GREEN = (0, 150, 0)    # Color for the ground
GRAY = (150, 150, 150)  # Color for the dinosaur
RED = (200, 0, 0)      # Color for pterodactyls
BROWN = (139, 69, 19)  # Color for ground detail

# Game properties
FPS = 60
INITIAL_GAME_SPEED = 5  # Initial speed at which obstacles and ground move
GRAVITY = 0.8           # Gravity applied to the dinosaur
JUMP_VELOCITY = -15     # Initial upward velocity when jumping

# Obstacle properties
MIN_CACTUS_WIDTH = 20
MAX_CACTUS_WIDTH = 40
MIN_CACTUS_HEIGHT = 40
MAX_CACTUS_HEIGHT = 80

MIN_PTERO_WIDTH = 50
MAX_PTERO_WIDTH = 70
MIN_PTERO_HEIGHT = 30
MAX_PTERO_HEIGHT = 40
# Pterodactyls can fly at different fixed heights
# These levels require the player to jump over them.
PTERO_Y_LEVELS = [SCREEN_HEIGHT - GROUND_HEIGHT - 100, SCREEN_HEIGHT - GROUND_HEIGHT - 150] 

# Scoring
SCORE_INCREMENT_INTERVAL = 1000  # Milliseconds per point (1000ms = 1 point per second as per design)

# Speed increase over time
SPEED_INCREASE_INTERVAL = 5000  # Milliseconds after which game speed increases
SPEED_INCREASE_AMOUNT = 0.5     # Amount to increase game speed by

# --- Screen Setup ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dino Dash")
clock = pygame.time.Clock()

# --- Fonts ---
font = pygame.font.Font(None, 36)          # Standard font for score
game_over_font = pygame.font.Font(None, 60) # Larger font for game over
restart_font = pygame.font.Font(None, 28)  # Smaller font for restart instructions

# --- Game Variables ---
game_over = False
score = 0
current_game_speed = INITIAL_GAME_SPEED
last_score_time = pygame.time.get_ticks()        # Tracks time for score increment
last_speed_increase_time = pygame.time.get_ticks() # Tracks time for speed increase

# --- Classes ---
class Dino:
    """Represents the player-controlled dinosaur."""
    def __init__(self):
        # Position the dino on the ground
        self.rect = pygame.Rect(50, SCREEN_HEIGHT - GROUND_HEIGHT - DINO_HEIGHT, DINO_WIDTH, DINO_HEIGHT)
        self.color = GRAY
        self.is_jumping = False
        self.jump_velocity = 0
        self.on_ground = True  # True if the dino is currently on the ground

    def jump(self):
        """Initiates a jump if the dino is on the ground."""
        if self.on_ground:
            self.is_jumping = True
            self.jump_velocity = JUMP_VELOCITY
            self.on_ground = False  # Dino is no longer on the ground

    def update(self):
        """Updates the dino's position, applying gravity."""
        if self.is_jumping:
            self.rect.y += self.jump_velocity
            self.jump_velocity += GRAVITY

            # Check if dino has landed back on the ground
            if self.rect.y >= SCREEN_HEIGHT - GROUND_HEIGHT - self.rect.height:
                self.rect.y = SCREEN_HEIGHT - GROUND_HEIGHT - self.rect.height # Snap to ground
                self.is_jumping = False
                self.jump_velocity = 0
                self.on_ground = True # Dino is back on the ground

    def draw(self, surface):
        """Draws the dino on the screen with a simple body and eye."""
        # Main body
        pygame.draw.rect(surface, self.color, self.rect)
        # Simple eye for character
        eye_x = self.rect.x + self.rect.width * 3 // 4
        eye_y = self.rect.y + self.rect.height // 4
        pygame.draw.circle(surface, BLACK, (eye_x, eye_y), 3)

class Ground:
    """Represents the scrolling ground plane."""
    def __init__(self):
        # Two segments for seamless scrolling
        self.segment1_rect = pygame.Rect(0, SCREEN_HEIGHT - GROUND_HEIGHT, SCREEN_WIDTH, GROUND_HEIGHT)
        self.segment2_rect = pygame.Rect(SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_HEIGHT, SCREEN_WIDTH, GROUND_HEIGHT)
        self.color = GREEN

    def update(self, speed):
        """Moves the ground segments to the left."""
        self.segment1_rect.x -= speed
        self.segment2_rect.x -= speed

        # Reset segments when they move completely off-screen to the left
        if self.segment1_rect.right < 0:
            self.segment1_rect.left = self.segment2_rect.right
        if self.segment2_rect.right < 0:
            self.segment2_rect.left = self.segment1_rect.right

    def draw(self, surface):
        """Draws both ground segments on the screen with simple texture."""
        pygame.draw.rect(surface, self.color, self.segment1_rect)
        pygame.draw.rect(surface, self.color, self.segment2_rect)

        # Add simple texture/lines to the ground for visual effect
        for rect in [self.segment1_rect, self.segment2_rect]:
            # Draw a few horizontal lines for a 'sandy' texture
            pygame.draw.line(surface, BROWN, (rect.x, rect.y + 10), (rect.x + rect.width, rect.y + 10), 1)
            pygame.draw.line(surface, BROWN, (rect.x, rect.y + 20), (rect.x + rect.width, rect.y + 20), 1)
            pygame.draw.line(surface, BROWN, (rect.x, rect.y + 30), (rect.x + rect.width, rect.y + 30), 1)


class Obstacle:
    """Base class for all obstacles."""
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color

    def update(self, speed):
        """Moves the obstacle to the left."""
        self.rect.x -= speed

    def draw(self, surface):
        """Draws the obstacle on the screen. To be overridden by subclasses for custom shapes."""
        pygame.draw.rect(surface, self.color, self.rect) # Default drawing for simple obstacles

class Cactus(Obstacle):
    """Represents a cactus obstacle with a slightly more distinct shape."""
    def __init__(self):
        width = random.randint(MIN_CACTUS_WIDTH, MAX_CACTUS_WIDTH)
        height = random.randint(MIN_CACTUS_HEIGHT, MAX_CACTUS_HEIGHT)
        # Position at the right edge of the screen, sitting on the ground
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_HEIGHT - height, width, height, BLACK)
    
    def draw(self, surface):
        """Draws a cactus with a main body and two small arms."""
        # Main body of the cactus
        pygame.draw.rect(surface, self.color, self.rect)
        # Add a couple of "arms" to make it look more like a cactus
        arm_width = self.rect.width // 3
        arm_height = self.rect.height // 3
        
        # Left arm
        pygame.draw.rect(surface, self.color, 
                         (self.rect.x - arm_width // 2, self.rect.y + arm_height, arm_width, arm_height))
        # Right arm
        pygame.draw.rect(surface, self.color, 
                         (self.rect.x + self.rect.width - arm_width // 2, self.rect.y + arm_height * 2 // 3, arm_width, arm_height))


class Pterodactyl(Obstacle):
    """Represents a flying pterodactyl obstacle with a simple body and wings."""
    def __init__(self):
        width = random.randint(MIN_PTERO_WIDTH, MAX_PTERO_WIDTH)
        height = random.randint(MIN_PTERO_HEIGHT, MAX_PTERO_HEIGHT)
        # Choose a random flying height
        y_pos = random.choice(PTERO_Y_LEVELS)
        # Position at the right edge of the screen at the chosen height
        super().__init__(SCREEN_WIDTH, y_pos, width, height, RED)

    def draw(self, surface):
        """Draws the pterodactyl with a simple body rectangle and two wing rectangles."""
        # Main body (smaller rectangle in the center)
        body_width = self.rect.width // 2
        body_height = self.rect.height
        body_rect = pygame.Rect(self.rect.x + self.rect.width // 4, self.rect.y, body_width, body_height)
        pygame.draw.rect(surface, self.color, body_rect) # Fix: use pygame.draw.rect

        # Wings (two smaller rectangles on either side of the body)
        wing_width = self.rect.width // 2.5
        wing_height = self.rect.height // 2
        
        # Left wing
        pygame.draw.rect(surface, self.color, 
                         (self.rect.x - wing_width + self.rect.width // 4, self.rect.y + wing_height // 2, wing_width, wing_height))
        # Right wing
        pygame.draw.rect(surface, self.color, 
                         (self.rect.x + self.rect.width // 2, self.rect.y + wing_height // 2, wing_width, wing_height))


# --- Game Objects ---
player = Dino()
ground = Ground()
obstacles = [] # List to hold current obstacles on screen

# Obstacle generation variables
next_obstacle_time = pygame.time.get_ticks() # Time when the next obstacle should spawn
obstacle_min_delay = 1000 # Minimum delay (ms) between obstacles
obstacle_max_delay = 2000 # Maximum delay (ms) between obstacles

# --- Game Functions ---
def reset_game():
    """Resets all game variables and objects to their initial state."""
    global game_over, score, current_game_speed, last_score_time, last_speed_increase_time, next_obstacle_time
    game_over = False
    score = 0
    current_game_speed = INITIAL_GAME_SPEED
    last_score_time = pygame.time.get_ticks()
    last_speed_increase_time = pygame.time.get_ticks()
    
    # Reset player state
    player.rect.y = SCREEN_HEIGHT - GROUND_HEIGHT - DINO_HEIGHT
    player.is_jumping = False
    player.jump_velocity = 0
    player.on_ground = True
    
    obstacles.clear() # Clear all existing obstacles
    
    # Set the time for the first obstacle after reset
    next_obstacle_time = pygame.time.get_ticks() + random.randint(obstacle_min_delay, obstacle_max_delay)

# --- Main Game Loop ---
while True:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit() # Exit the game gracefully
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                if not game_over:
                    player.jump() # Allow jump only if game is not over
            if event.key == pygame.K_r:
                if game_over:
                    reset_game() # Allow restart only if game is over

    if not game_over:
        # --- Update Game State ---
        player.update()
        ground.update(current_game_speed)

        # Obstacle Generation Logic
        now = pygame.time.get_ticks()
        if now >= next_obstacle_time:
            # Randomly decide between spawning a Cactus or a Pterodactyl
            if random.randint(0, 1) == 0: # 0 for Cactus
                obstacles.append(Cactus())
            else: # 1 for Pterodactyl
                obstacles.append(Pterodactyl())
            
            # Set time for the next obstacle spawn
            next_obstacle_time = now + random.randint(obstacle_min_delay, obstacle_max_delay)

        # Update and remove obstacles that have moved off-screen
        # Use list(obstacles) to iterate over a copy, allowing modification of original list
        for obstacle in list(obstacles):
            obstacle.update(current_game_speed)
            if obstacle.rect.right < 0:
                obstacles.remove(obstacle)

        # Collision Detection
        for obstacle in obstacles:
            if player.rect.colliderect(obstacle.rect):
                game_over = True # End the game upon collision

        # Score Update
        if now - last_score_time >= SCORE_INCREMENT_INTERVAL:
            score += 1
            last_score_time = now

        # Increase Game Speed Over Time
        if now - last_speed_increase_time >= SPEED_INCREASE_INTERVAL:
            current_game_speed += SPEED_INCREASE_AMOUNT
            last_speed_increase_time = now

    # --- Drawing ---
    screen.fill(WHITE) # Fill the background with white (desert sky)

    ground.draw(screen)
    player.draw(screen)
    for obstacle in obstacles:
        obstacle.draw(screen)

    # Display Current Score
    score_text = font.render(f"Score: {score}", True, BLACK)
    # Position score at the top right
    screen.blit(score_text, (SCREEN_WIDTH - score_text.get_width() - 10, 10))

    if game_over:
        # Display Game Over message
        game_over_text = game_over_font.render("GAME OVER", True, BLACK)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        screen.blit(game_over_text, game_over_rect)

        # Display Final Score
        final_score_text = font.render(f"Final Score: {score}", True, BLACK)
        final_score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        screen.blit(final_score_text, final_score_rect)

        # Display Restart Instruction
        restart_text = restart_font.render("Press 'R' to Restart", True, BLACK)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        screen.blit(restart_text, restart_rect)

    pygame.display.flip() # Update the full display Surface to the screen
    clock.tick(FPS)       # Control the game's frame rate
