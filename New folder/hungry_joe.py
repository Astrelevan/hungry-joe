
import pygame
import random
import math
import time
import os
import sys
from collections import deque

# --------------------- Initialize Pygame ---------------------
pygame.init()

# --------------------- Constants and Configurations ---------------------

# Screen dimensions
WIDTH, HEIGHT = 800, 600

# Frame rate
FPS = 60

# Player (Joe Biden) speed in pixels per second
PLAYER_SPEED = 200

# Cat speed configurations
CAT_START_SPEED = 30          # Starting speed
CAT_MAX_SPEED = PLAYER_SPEED  # Maximum speed equals player's speed
SPEED_INCREASE = 5            # Speed increase per second

# Image scaling factors
IMAGE_SCALE_FACTOR = 0.7       # Make images 30% smaller
JOE_WIDENING_FACTOR = 1.3      # Widen Joe Biden's image by 30%

# Original character dimensions before scaling
ORIGINAL_CHAR_WIDTH = 100
ORIGINAL_CHAR_HEIGHT = 140

# Calculated character dimensions after scaling
SCALED_CHAR_WIDTH = int(ORIGINAL_CHAR_WIDTH * IMAGE_SCALE_FACTOR)   # 70
SCALED_CHAR_HEIGHT = int(ORIGINAL_CHAR_HEIGHT * IMAGE_SCALE_FACTOR) # 98

# Joe Biden's width after widening
JOE_WIDTH = int(SCALED_CHAR_WIDTH * JOE_WIDENING_FACTOR)           # ~91
JOE_HEIGHT = SCALED_CHAR_HEIGHT                                   # 98

# Projectile configurations
PROJECTILE_SPEED_MULTIPLIER = 2  # Projectile speed is 2x the cat's speed
PROJECTILE_SIZE = 10              # Radius of the projectile
PROJECTILE_COLOR = (0, 255, 0)    # Green color for projectile

# Projectile firing configurations
PROJECTILE_START_TIME = 10       # Start firing projectiles after 10 seconds
PROJECTILE_INTERVAL = 2          # Fire a projectile every 2 seconds

# Collision delay with the cat
CAT_COLLISION_DELAY = 0.2         # 0.2 seconds

# Reaction delay for the cat
CAT_REACTION_DELAY = 0.5           # 0.5 seconds

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# --------------------- Screen Setup ---------------------
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hungry Joe")

# --------------------- Load and Scale Images ---------------------

def load_and_scale_image(path, width, height):
    """
    Loads an image from the specified path and scales it to the given width and height.
    """
    try:
        image = pygame.image.load(path).convert_alpha()
        image = pygame.transform.scale(image, (width, height))
        print(f"✅ Loaded and scaled image: {path} to ({width}x{height})")
        return image
    except pygame.error as e:
        print(f"❌ Unable to load image at {path}: {e}")
        pygame.quit()
        sys.exit()

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define image paths
joe_img_path = os.path.join(script_dir, "joe_biden.png")
cat_img_path = os.path.join(script_dir, "cat.png")

# Load and scale images
joe_img_original = load_and_scale_image(joe_img_path, JOE_WIDTH, JOE_HEIGHT)
cat_img_original = load_and_scale_image(cat_img_path, SCALED_CHAR_WIDTH, SCALED_CHAR_HEIGHT)

# --------------------- Leaderboard Setup ---------------------
leaderboard = []

def update_leaderboard(time_survived):
    """
    Updates the leaderboard with the latest survival time.
    Keeps only the top 5 scores.
    """
    leaderboard.append(time_survived)
    leaderboard.sort(reverse=True)
    if len(leaderboard) > 5:
        leaderboard.pop()

def display_leaderboard():
    """
    Displays the leaderboard on the screen.
    """
    y_offset = 0
    leaderboard_text = font.render("Leaderboard:", True, BLACK)
    screen.blit(leaderboard_text, (10, 10))
    y_offset += 40
    for i, score in enumerate(leaderboard):
        score_text = font.render(f"{i+1}. Survived {score:.2f} sec", True, BLACK)
        screen.blit(score_text, (10, 10 + y_offset))
        y_offset += 30

# --------------------- Font Setup ---------------------
font = pygame.font.Font(None, 36)

# --------------------- Helper Functions ---------------------

def rotate_image(image, direction):
    """
    Rotates the image based on the direction.
    Assumes original image faces left.
    """
    if direction == 'up':
        rotated_image = pygame.transform.rotate(image, 90)
    elif direction == 'down':
        rotated_image = pygame.transform.rotate(image, -90)
    elif direction == 'left':
        rotated_image = image  # Original image faces left
    elif direction == 'right':
        rotated_image = pygame.transform.flip(image, True, False)
    else:
        rotated_image = image
    return rotated_image

def show_game_over_screen(time_survived):
    """
    Displays the game over screen with the time survived.
    """
    screen.fill(WHITE)
    message = font.render("You have been eaten!", True, BLACK)
    time_message = font.render(f"Time Survived: {time_survived:.2f} sec", True, BLACK)
    prompt = font.render("Press any key to play again.", True, BLACK)
    
    screen.blit(message, (WIDTH // 2 - message.get_width() // 2, HEIGHT // 2 - 60))
    screen.blit(time_message, (WIDTH // 2 - time_message.get_width() // 2, HEIGHT // 2))
    screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT // 2 + 60))
    
    pygame.display.flip()
    wait_for_key()

def wait_for_key():
    """
    Waits for the user to press any key to restart the game.
    """
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                waiting = False

# --------------------- Main Game Function ---------------------

def game():
    """
    The main game loop.
    """
    clock = pygame.time.Clock()
    start_time = time.time()
    projectile_fired = False      # Flag to track if projectile has been fired
    last_projectile_time = 0      # Time when the last projectile was fired
    collision_timer = 0           # Timer to track collision duration with cat
    projectile_active = False     # Flag to track if projectile is active
    projectile_x = None
    projectile_y = None
    projectile_dx = 0
    projectile_dy = 0
    
    # Starting positions
    player_x = WIDTH - JOE_WIDTH - 10     # Slight offset from the edge
    player_y = HEIGHT // 2 - JOE_HEIGHT // 2
    cat_x = 10                            # Slight offset from the edge
    cat_y = random.randint(0, HEIGHT - SCALED_CHAR_HEIGHT)
    
    player_speed_x = 0
    player_speed_y = 0
    cat_speed = CAT_START_SPEED
    
    player_direction = 'left'
    cat_direction = 'right'
    
    # For delayed reaction, store Joe's position history
    position_history = deque()
    
    running = True
    while running:
        dt = clock.tick(FPS) / 1000  # Delta time in seconds
        current_time = time.time()
        time_survived = current_time - start_time
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    player_speed_y = -PLAYER_SPEED
                    player_direction = 'up'
                elif event.key == pygame.K_DOWN:
                    player_speed_y = PLAYER_SPEED
                    player_direction = 'down'
                elif event.key == pygame.K_LEFT:
                    player_speed_x = -PLAYER_SPEED
                    player_direction = 'left'
                elif event.key == pygame.K_RIGHT:
                    player_speed_x = PLAYER_SPEED
                    player_direction = 'right'
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    player_speed_y = 0
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    player_speed_x = 0
        
        # Move Player
        player_x += player_speed_x * dt
        player_y += player_speed_y * dt
        
        # Boundaries for Player
        player_x = max(0, min(WIDTH - JOE_WIDTH, player_x))
        player_y = max(0, min(HEIGHT - JOE_HEIGHT, player_y))
        
        # Record current position with timestamp for delayed reaction
        position_history.append((current_time, player_x, player_y))
        
        # Remove old positions beyond the reaction delay
        while position_history and position_history[0][0] < current_time - CAT_REACTION_DELAY:
            position_history.popleft()
        
        # Get Joe's position from CAT_REACTION_DELAY seconds ago
        if position_history and position_history[0][0] <= current_time - CAT_REACTION_DELAY:
            delayed_player_x, delayed_player_y = position_history[0][1], position_history[0][2]
        elif position_history:
            # If exact timestamp not found, use the oldest available
            delayed_player_x, delayed_player_y = position_history[0][1], position_history[0][2]
        else:
            delayed_player_x, delayed_player_y = player_x, player_y  # Fallback to current position
        
        # Move Cat towards delayed Player position
        dx = delayed_player_x - cat_x
        dy = delayed_player_y - cat_y
        distance = math.hypot(dx, dy)
        if distance != 0:
            dx_norm = dx / distance
            dy_norm = dy / distance
        else:
            dx_norm = dy_norm = 0
        
        # Increase cat's speed over time, but cap it at PLAYER_SPEED
        cat_speed += SPEED_INCREASE * dt
        if cat_speed > CAT_MAX_SPEED:
            cat_speed = CAT_MAX_SPEED
        
        cat_x += dx_norm * cat_speed * dt
        cat_y += dy_norm * cat_speed * dt
        
        # Update Cat direction
        if abs(dx) > abs(dy):
            if dx > 0:
                cat_direction = 'right'
            else:
                cat_direction = 'left'
        else:
            if dy > 0:
                cat_direction = 'down'
            else:
                cat_direction = 'up'
        
        # Check if it's time to fire a projectile
        if time_survived >= PROJECTILE_START_TIME:
            if (current_time - last_projectile_time) >= PROJECTILE_INTERVAL:
                # Calculate direction towards current player position
                proj_dx = player_x - cat_x
                proj_dy = player_y - cat_y
                proj_distance = math.hypot(proj_dx, proj_dy)
                if proj_distance != 0:
                    proj_dx_norm = proj_dx / proj_distance
                    proj_dy_norm = proj_dy / proj_distance
                else:
                    proj_dx_norm = proj_dy_norm = 0
                
                # Set projectile speed
                projectile_speed = cat_speed * PROJECTILE_SPEED_MULTIPLIER
                
                # Initialize projectile position at cat's current position (center)
                projectile_x = cat_x + SCALED_CHAR_WIDTH // 2
                projectile_y = cat_y + SCALED_CHAR_HEIGHT // 2
                
                # Set projectile movement vector
                projectile_dx = proj_dx_norm * projectile_speed
                projectile_dy = proj_dy_norm * projectile_speed
                
                projectile_active = True
                last_projectile_time = current_time
                print(f"🕹️ Projectile fired towards ({player_x:.2f}, {player_y:.2f}) with speed {projectile_speed:.2f}")
        
        # Update projectile position
        if projectile_active:
            projectile_x += projectile_dx * dt
            projectile_y += projectile_dy * dt
            
            # Check if projectile is off-screen
            if (projectile_x < 0 or projectile_x > WIDTH or
                projectile_y < 0 or projectile_y > HEIGHT):
                projectile_active = False
                print("🛑 Projectile went off-screen.")
        
        # Drawing
        screen.fill(WHITE)
        
        # Rotate images based on direction
        player_img = rotate_image(joe_img_original, player_direction)
        cat_img = rotate_image(cat_img_original, cat_direction)
        
        # Draw Player and Cat
        screen.blit(player_img, (player_x, player_y))
        screen.blit(cat_img, (cat_x, cat_y))
        
        # Draw Projectile if active
        if projectile_active:
            pygame.draw.circle(screen, PROJECTILE_COLOR, (int(projectile_x), int(projectile_y)), PROJECTILE_SIZE)
        
        # Display time survived
        time_text = font.render(f"Time Survived: {time_survived:.2f} sec", True, BLACK)
        screen.blit(time_text, (WIDTH - 300, 10))
        
        # Display the leaderboard
        display_leaderboard()
        
        pygame.display.flip()
        
        # Collision Detection with Cat
        player_rect = pygame.Rect(player_x, player_y, JOE_WIDTH, JOE_HEIGHT)
        cat_rect = pygame.Rect(cat_x, cat_y, SCALED_CHAR_WIDTH, SCALED_CHAR_HEIGHT)
        
        if player_rect.colliderect(cat_rect):
            collision_timer += dt
            if collision_timer >= CAT_COLLISION_DELAY:
                print("💀 Collision with cat detected. Game Over.")
                return time_survived
        else:
            collision_timer = 0  # Reset timer if not colliding
        
        # Collision Detection with Projectile
        if projectile_active:
            projectile_rect = pygame.Rect(projectile_x - PROJECTILE_SIZE, projectile_y - PROJECTILE_SIZE,
                                         PROJECTILE_SIZE * 2, PROJECTILE_SIZE * 2)
            if player_rect.colliderect(projectile_rect):
                print("💥 Hit by projectile! Game Over.")
                return time_survived

# --------------------- Main Execution ---------------------

if __name__ == "__main__":
    try:
        while True:
            time_survived = game()
            update_leaderboard(time_survived)
            show_game_over_screen(time_survived)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        pygame.quit()
        sys.exit()
