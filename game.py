import os
import sys
import random
import pygame
import math

# ==================== Setup ====================
if not os.environ.get("DISPLAY"):
    os.environ["DISPLAY"] = ":99"
if not os.environ.get("XDG_RUNTIME_DIR"):
    os.environ["XDG_RUNTIME_DIR"] = "/tmp/runtime-vscode"
    os.makedirs("/tmp/runtime-vscode", exist_ok=True)

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Sword Slayer")
clock = pygame.time.Clock()
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (40, 40, 40)
YELLOW = (255, 220, 0)

# Player
player_size = 40
player = pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, player_size, player_size)
player_speed = 5

# Sword (vertical, wider, shorter range)
sword_active = False
sword_timer = 0
SWORD_DURATION = 10
SWORD_RANGE = 48
SWORD_WIDTH = 58

sword_direction = "right"

# Enemies
enemies = []
ENEMY_SIZE = 36
base_spawn_rate = 90          # Gentle at start
ENEMY_SPEED_BASE = 1.8
MIN_SPAWN_DISTANCE = 250      # Much safer distance

spawn_timer = 0

# Score & Difficulty
score = 0
score_start_time = pygame.time.get_ticks()
font = pygame.font.Font(None, 36)
game_over = False
running = True

def spawn_enemy():
    """Spawn ONLY from left or right, far from player"""
    attempts = 0
    while attempts < 30:   # safety to prevent infinite loop
        side = random.choice(["left", "right"])
        
        if side == "left":
            x = -ENEMY_SIZE - 20
            y = random.randint(30, SCREEN_HEIGHT - ENEMY_SIZE - 30)
        else:
            x = SCREEN_WIDTH + 20
            y = random.randint(30, SCREEN_HEIGHT - ENEMY_SIZE - 30)
        
        enemy = pygame.Rect(x, y, ENEMY_SIZE, ENEMY_SIZE)
        
        # Check distance from player
        dist = math.hypot(enemy.centerx - player.centerx, enemy.centery - player.centery)
        if dist >= MIN_SPAWN_DISTANCE:
            enemies.append(enemy)
            return
        
        attempts += 1
    
    # Fallback (very rare): spawn on the far side
    side = random.choice(["left", "right"])
    x = -ENEMY_SIZE - 20 if side == "left" else SCREEN_WIDTH + 20
    y = random.randint(30, SCREEN_HEIGHT - ENEMY_SIZE - 30)
    enemies.append(pygame.Rect(x, y, ENEMY_SIZE, ENEMY_SIZE))

def get_sword_rect():
    if not sword_active:
        return None

    if sword_direction == "right":
        return pygame.Rect(player.right, player.centery - SWORD_WIDTH//2, SWORD_RANGE, SWORD_WIDTH)
    elif sword_direction == "left":
        return pygame.Rect(player.left - SWORD_RANGE, player.centery - SWORD_WIDTH//2, SWORD_RANGE, SWORD_WIDTH)
    elif sword_direction == "up":
        return pygame.Rect(player.centerx - SWORD_WIDTH//2, player.top - SWORD_RANGE, SWORD_WIDTH, SWORD_RANGE)
    elif sword_direction == "down":
        return pygame.Rect(player.centerx - SWORD_WIDTH//2, player.bottom, SWORD_WIDTH, SWORD_RANGE)

# ==================== MAIN LOOP ====================
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and not game_over:
            if event.key == pygame.K_ESCAPE:
                running = False

    if game_over:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            player.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            enemies.clear()
            score = 0
            score_start_time = pygame.time.get_ticks()
            spawn_timer = 0
            game_over = False
        continue

    # ==================== INPUT ====================
    keys = pygame.key.get_pressed()

    # Movement - WASD only
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:   player.x -= player_speed
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:  player.x += player_speed
    if keys[pygame.K_w] or keys[pygame.K_UP]:     player.y -= player_speed
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:   player.y += player_speed

    # Sword - Arrow keys only
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
    player.clamp_ip(screen.get_rect())

    if sword_active:
        sword_timer -= 1
        if sword_timer <= 0:
            sword_active = False

    # Difficulty
    current_score = (pygame.time.get_ticks() - score_start_time) // 100
    spawn_rate = max(35, base_spawn_rate - (current_score // 22))

    spawn_timer += 1
    if spawn_timer >= spawn_rate:
        spawn_enemy()
        spawn_timer = 0

    difficulty_multiplier = 1 + (current_score // 80) * 0.25

    # Update enemies
    for enemy in enemies[:]:
        dx = player.centerx - enemy.centerx
        dy = player.centery - enemy.centery
        dist = (dx**2 + dy**2)**0.5 or 1

        speed = ENEMY_SPEED_BASE * difficulty_multiplier
        enemy.x += (dx / dist) * speed
        enemy.y += (dy / dist) * speed

        # Sword hit
        sword_rect = get_sword_rect()
        if sword_rect and sword_rect.colliderect(enemy):
            enemies.remove(enemy)
            continue

        # Player hit
        if player.colliderect(enemy):
            game_over = True

    score = current_score

    # ==================== RENDER ====================
    screen.fill(BLACK)

    # Grid
    for x in range(0, SCREEN_WIDTH, 40):
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, 40):
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))

    pygame.draw.rect(screen, GREEN, player)

    if sword_active:
        sword_rect = get_sword_rect()
        if sword_rect:
            pygame.draw.rect(screen, YELLOW, sword_rect, border_radius=6)

    for enemy in enemies:
        pygame.draw.rect(screen, RED, enemy)

    # UI
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (15, 10))
    level_text = font.render(f"Level: {(score // 80) + 1}", True, WHITE)
    screen.blit(level_text, (15, 50))

    if game_over:
        go_text = font.render("GAME OVER - Press R to Restart", True, RED)
        screen.blit(go_text, (SCREEN_WIDTH//2 - 230, SCREEN_HEIGHT//2))

    pygame.display.flip()

pygame.quit()
sys.exit()
