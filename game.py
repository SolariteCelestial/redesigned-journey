import os
import sys
import random
import pygame

# ==================== Headless / Codespaces fixes ====================
if not os.environ.get("DISPLAY"):
    os.environ["DISPLAY"] = ":99"
if not os.environ.get("XDG_RUNTIME_DIR"):
    os.environ["XDG_RUNTIME_DIR"] = "/tmp/runtime-vscode"
    os.makedirs("/tmp/runtime-vscode", exist_ok=True)

pygame.init()

# ==================== SCREEN SETUP ====================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TITLE = "Sword Slayer"

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()
FPS = 60

# ==================== COLORS ====================
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (40, 40, 40)
YELLOW = (255, 255, 0)

# ==================== PLAYER ====================
player_size = 40
player = pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, player_size, player_size)
player_speed = 5

# ==================== SWORD ====================
sword_length = 50
sword_active = False
sword_timer = 0
SWORD_DURATION = 8   # frames the sword stays out
sword_direction = "right"  # "up", "down", "left", "right"

# ==================== ENEMIES ====================
enemies = []
ENEMY_SIZE = 35
base_spawn_rate = 60   # frames between spawns at start
spawn_timer = 0
ENEMY_SPEED_BASE = 2.5

# ==================== SCORE & DIFFICULTY ====================
score = 0
score_start_time = pygame.time.get_ticks()
font = pygame.font.Font(None, 36)
game_over = False
running = True

# Simple hit sound (we'll use a beep since chord.wav may not exist)
try:
    hit_sound = pygame.mixer.Sound("chord.wav")
except:
    # Fallback: generate a simple hit sound
    hit_sound = None

def spawn_enemy():
    side = random.choice(["left", "right", "top", "bottom"])
    
    if side == "left":
        x = -ENEMY_SIZE
        y = random.randint(0, SCREEN_HEIGHT - ENEMY_SIZE)
    elif side == "right":
        x = SCREEN_WIDTH
        y = random.randint(0, SCREEN_HEIGHT - ENEMY_SIZE)
    elif side == "top":
        x = random.randint(0, SCREEN_WIDTH - ENEMY_SIZE)
        y = -ENEMY_SIZE
    else:  # bottom
        x = random.randint(0, SCREEN_WIDTH - ENEMY_SIZE)
        y = SCREEN_HEIGHT
    
    enemy = pygame.Rect(x, y, ENEMY_SIZE, ENEMY_SIZE)
    enemies.append(enemy)

def get_sword_rect():
    """Returns the current sword hitbox based on direction"""
    if not sword_active:
        return None
    
    if sword_direction == "right":
        return pygame.Rect(player.right, player.centery - 15, sword_length, 30)
    elif sword_direction == "left":
        return pygame.Rect(player.left - sword_length, player.centery - 15, sword_length, 30)
    elif sword_direction == "up":
        return pygame.Rect(player.centerx - 15, player.top - sword_length, 30, sword_length)
    elif sword_direction == "down":
        return pygame.Rect(player.centerx - 15, player.bottom, 30, sword_length)

# ==================== MAIN GAME LOOP ====================
while running:
    dt = clock.tick(FPS)  # not really using dt yet, but good to have

    # ==================== EVENT HANDLING ====================
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and not game_over:
            if event.key == pygame.K_ESCAPE:
                running = False

    if game_over:
        # Simple restart with R key
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            # Reset game
            player.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            enemies.clear()
            score = 0
            score_start_time = pygame.time.get_ticks()
            game_over = False
        continue

    # ==================== INPUT ====================
    keys = pygame.key.get_pressed()

    # Movement - WASD
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        player.x -= player_speed
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        player.x += player_speed
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        player.y -= player_speed
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        player.y += player_speed

    # Sword attack - Arrow keys
    if not sword_active:
        if keys[pygame.K_RIGHT]:
            sword_direction = "right"
            sword_active = True
            sword_timer = SWORD_DURATION
        elif keys[pygame.K_LEFT]:
            sword_direction = "left"
            sword_active = True
            sword_timer = SWORD_DURATION
        elif keys[pygame.K_UP]:
            sword_direction = "up"
            sword_active = True
            sword_timer = SWORD_DURATION
        elif keys[pygame.K_DOWN]:
            sword_direction = "down"
            sword_active = True
            sword_timer = SWORD_DURATION

    # ==================== UPDATE ====================
    # Keep player in bounds
    player.clamp_ip(screen.get_rect())

    # Sword timer
    if sword_active:
        sword_timer -= 1
        if sword_timer <= 0:
            sword_active = False

    # Spawn enemies (gets faster over time)
    current_score = (pygame.time.get_ticks() - score_start_time) // 100
    spawn_rate = max(15, base_spawn_rate - (current_score // 20))  # faster spawning

    spawn_timer += 1
    if spawn_timer >= spawn_rate:
        spawn_enemy()
        spawn_timer = 0

    # Update enemies
    difficulty_multiplier = 1 + (current_score // 40) * 0.3  # speed increases gradually

    for enemy in enemies[:]:
        # Move toward player (simple AI)
        dx = player.centerx - enemy.centerx
        dy = player.centery - enemy.centery
        dist = (dx**2 + dy**2)**0.5
        
        if dist > 0:
            enemy.x += (dx / dist) * ENEMY_SPEED_BASE * difficulty_multiplier
            enemy.y += (dy / dist) * ENEMY_SPEED_BASE * difficulty_multiplier

        # Check collision with sword
        sword_rect = get_sword_rect()
        if sword_rect and sword_rect.colliderect(enemy):
            if hit_sound:
                hit_sound.play()
            enemies.remove(enemy)
            continue

        # Check collision with player → Game Over
        if player.colliderect(enemy):
            game_over = True
            if hit_sound:
                hit_sound.play()

    # Update score (increases with time)
    score = (pygame.time.get_ticks() - score_start_time) // 100

    # ==================== RENDER ====================
    screen.fill(BLACK)

    # Draw subtle grid
    for x in range(0, SCREEN_WIDTH, 40):
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, 40):
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))

    # Draw player (green square)
    pygame.draw.rect(screen, GREEN, player)

    # Draw sword when active
    if sword_active:
        sword_rect = get_sword_rect()
        if sword_rect:
            pygame.draw.rect(screen, YELLOW, sword_rect)

    # Draw enemies (red)
    for enemy in enemies:
        pygame.draw.rect(screen, RED, enemy)

    # UI
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    difficulty_text = font.render(f"Level: {(score // 50) + 1}", True, WHITE)
    screen.blit(difficulty_text, (10, 50))

    if game_over:
        game_over_text = font.render("GAME OVER - Press R to Restart", True, RED)
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2))

    pygame.display.flip()

pygame.quit()
sys.exit()
