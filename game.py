import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Game Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
GROUND_HEIGHT = 50
PLAYER_WIDTH = 30
PLAYER_HEIGHT = 50
OBSTACLE_WIDTH = 20
OBSTACLE_HEIGHT_MIN = 30
OBSTACLE_HEIGHT_MAX = 70
GAP_WIDTH_MIN = 80
GAP_WIDTH_MAX = 150
# Spacing between the end of one obstacle/gap and the start of the next one
MIN_GAP_BETWEEN_OBSTACLES = 150
MAX_GAP_BETWEEN_OBSTACLES = 300
PLAYER_X = 100  # Fixed X position for the player
INITIAL_GAME_SPEED = 5.0 # Use float for gradual speed increase
GRAVITY = 0.8
JUMP_VELOCITY = -15  # Initial upward velocity for jump
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
LIGHT_BLUE = (173, 216, 230) # Background sky color

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pixel Jumper")

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Font for score and game over messages
font = pygame.font.Font(None, 36)
game_over_font = pygame.font.Font(None, 72)

# Player Class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface([PLAYER_WIDTH, PLAYER_HEIGHT])
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.x = PLAYER_X
        # Player starts on the ground
        self.rect.y = SCREEN_HEIGHT - GROUND_HEIGHT - PLAYER_HEIGHT
        self.y_velocity = 0
        self.is_jumping = False
        self.is_falling = False

    def update(self):
        # Apply gravity to simulate falling
        self.y_velocity += GRAVITY
        self.rect.y += self.y_velocity

        # Ground collision logic
        if self.rect.y >= SCREEN_HEIGHT - GROUND_HEIGHT - PLAYER_HEIGHT:
            self.rect.y = SCREEN_HEIGHT - GROUND_HEIGHT - PLAYER_HEIGHT
            self.y_velocity = 0
            self.is_jumping = False
            self.is_falling = False
        elif self.y_velocity > 0: # Player is moving downwards
            self.is_falling = True
            self.is_jumping = False
        elif self.y_velocity < 0: # Player is moving upwards
            self.is_falling = False
            self.is_jumping = True

    def jump(self):
        # Allow jump only if player is on the ground and not already jumping/falling
        if self.rect.y == SCREEN_HEIGHT - GROUND_HEIGHT - PLAYER_HEIGHT and self.y_velocity == 0:
            self.is_jumping = True
            self.is_falling = False # Ensure not falling when starting a jump
            self.y_velocity = JUMP_VELOCITY # Give upward velocity

# Obstacle Class (for spike blocks and gaps)
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, width, height, is_gap=False):
        super().__init__()
        self.is_gap = is_gap
        if not self.is_gap:
            # Spike block: visible, solid, positioned on the ground
            self.image = pygame.Surface([width, height])
            self.image.fill(RED)
            self.rect = self.image.get_rect()
            self.rect.x = x
            # Position spike blocks on top of the ground
            self.rect.y = SCREEN_HEIGHT - GROUND_HEIGHT - height
        else:
            # Gap: invisible, represents missing ground. Its rect defines the "hole" area.
            # Using SRCALPHA makes the surface transparent.
            self.image = pygame.Surface([width, height], pygame.SRCALPHA) 
            self.image.fill((0,0,0,0)) # Completely transparent
            self.rect = self.image.get_rect()
            self.rect.x = x
            # Gaps effectively occupy the ground space for collision detection
            self.rect.y = SCREEN_HEIGHT - GROUND_HEIGHT

    def update(self):
        self.rect.x -= GAME_SPEED
        # Remove obstacle if it moves off-screen to the left
        if self.rect.right < 0:
            self.kill() # Removes the sprite from all groups it belongs to

# Game Variables (initialized for the first game)
player = Player()
obstacles = pygame.sprite.Group()
score = 0
game_over = False
distance_travelled = 0
# `next_obstacle_spawn_x` tracks the minimum X coordinate where the next obstacle can begin.
# This ensures proper spacing between consecutive obstacles.
next_obstacle_spawn_x = SCREEN_WIDTH 
GAME_SPEED = INITIAL_GAME_SPEED

def reset_game():
    """Resets all game variables to their initial state for a new game."""
    global player, obstacles, score, game_over, distance_travelled, next_obstacle_spawn_x, GAME_SPEED
    player = Player()
    obstacles.empty() # Clear all existing obstacles
    score = 0
    game_over = False
    distance_travelled = 0
    next_obstacle_spawn_x = SCREEN_WIDTH # Reset for new game
    GAME_SPEED = INITIAL_GAME_SPEED # Reset speed to initial value

# --- Main Game Loop ---
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                if game_over:
                    reset_game() # Restart the game if it's over
                else:
                    player.jump() # Make the player jump

    if not game_over:
        # Update game elements
        player.update()
        obstacles.update()

        # Obstacle generation logic
        # Spawn a new obstacle only when there's enough space since the last one.
        # This prevents obstacles from spawning too close to each other, ensuring a clear gap.
        if SCREEN_WIDTH >= next_obstacle_spawn_x:
            # Determine the type of obstacle to spawn randomly
            choice = random.choice(["spike", "gap"])
            new_obstacle = None
            
            if choice == "spike":
                obs_height = random.randint(OBSTACLE_HEIGHT_MIN, OBSTACLE_HEIGHT_MAX)
                # Obstacles always start at the right edge of the screen
                new_obstacle = Obstacle(SCREEN_WIDTH, OBSTACLE_WIDTH, obs_height)
            elif choice == "gap":
                gap_width = random.randint(GAP_WIDTH_MIN, GAP_WIDTH_MAX)
                # Gaps have a height equal to GROUND_HEIGHT so their rect covers the ground area
                new_obstacle = Obstacle(SCREEN_WIDTH, gap_width, GROUND_HEIGHT, is_gap=True)
            
            if new_obstacle:
                obstacles.add(new_obstacle)
                # Calculate the next spawn point: current obstacle's right edge + a random gap
                next_obstacle_spawn_x = new_obstacle.rect.right + random.randint(MIN_GAP_BETWEEN_OBSTACLES, MAX_GAP_BETWEEN_OBSTACLES)

        # Collision detection
        for obstacle in obstacles:
            if player.rect.colliderect(obstacle.rect):
                if not obstacle.is_gap:
                    # Collision with a visible spike block results in game over
                    game_over = True
                else:
                    # Collision with a gap: player falls into it if not successfully jumping over.
                    # This occurs if player's bottom hits or goes below ground level while inside the gap's X range.
                    if player.rect.bottom >= SCREEN_HEIGHT - GROUND_HEIGHT:
                        game_over = True
        
        # Score update: based on distance travelled
        distance_travelled += GAME_SPEED
        score = int(distance_travelled // 10) # 1 point per 10 pixels

        # Difficulty scaling: gradually increase game speed
        # This triggers every 1000 pixels travelled, increasing speed by 0.1
        if distance_travelled % 1000 < GAME_SPEED and distance_travelled > 0: # Check avoids continuous increment for one block
            GAME_SPEED += 0.1

    # --- Drawing ---
    screen.fill(LIGHT_BLUE) # Background color (sky)

    # Draw ground
    pygame.draw.rect(screen, GREEN, (0, SCREEN_HEIGHT - GROUND_HEIGHT, SCREEN_WIDTH, GROUND_HEIGHT))

    # Draw obstacles (only visible spike blocks, gaps are invisible)
    for obs in obstacles:
        if not obs.is_gap:
            screen.blit(obs.image, obs.rect)

    # Draw player
    screen.blit(player.image, player.rect)

    # Draw score
    score_text = font.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (10, 10))

    # Display Game Over message and restart prompt
    if game_over:
        game_over_text = game_over_font.render("GAME OVER", True, BLACK)
        restart_text = font.render("Press SPACE to Restart", True, BLACK)
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(FPS)

# Quit Pygame
pygame.quit()
sys.exit()
