"""Game logic and main game loop for Rabbit Adventure."""

import cv2
import mediapipe as mp
import os
import pygame
import random
from config import TILE, MAPS_FOLDER
from texture_loader import load_textures_with_size, create_player_textures
from ui import draw_game
from level_loader import get_levels

# Load levels from file with validation
LEVELS = get_levels()
GESTURE_COOLDOWN = 300
FIST_HOLD_TIME = 700
ZONE_LOW = 0.35
ZONE_HIGH = 0.65

def is_fist(hand_landmarks):
    fingertips = [8, 12, 16, 20]
    pip_joints = [6, 10, 14, 18]
    folded = 0

    for tip, pip in zip(fingertips, pip_joints):
        if hand_landmarks[tip].y > hand_landmarks[pip].y:
            folded += 1

    return folded >= 4

def process_camera_frame(cap, detector, gesture_state):
    """Read one webcam frame, run hand detection, and show the preview."""
    ret, frame = cap.read()
    if not ret or frame is None:
        print("Warning: failed to read camera frame; skipping this frame")
        cv2.waitKey(1)
        return None, False

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    result = detector.detect(mp_image)

    direction = None
    now = pygame.time.get_ticks()
    if result.hand_landmarks:
        hand = result.hand_landmarks[0]
        index_tip = hand[8]
        height, width = frame.shape[:2]
        index_coords = (int(index_tip.x * width), int(index_tip.y * height))
        cv2.circle(frame, index_coords, 8, (0, 255, 0), -1)

        if is_fist(hand):
            if gesture_state["fist_started_at"] is None:
                gesture_state["fist_started_at"] = now
            if now - gesture_state["fist_started_at"] >= FIST_HOLD_TIME:
                cv2.imshow("Camera Preview", frame)
                cv2.waitKey(1)
                return None, True
        else:
            gesture_state["fist_started_at"] = None
            if now - gesture_state["last_move_at"] >= GESTURE_COOLDOWN:
                if index_tip.y < ZONE_LOW:
                    direction = "up"
                elif index_tip.y > ZONE_HIGH:
                    direction = "down"
                elif index_tip.x < ZONE_LOW:
                    direction = "left"
                elif index_tip.x > ZONE_HIGH:
                    direction = "right"

                if direction is not None:
                    gesture_state["last_move_at"] = now

    else:
        gesture_state["fist_started_at"] = None

    cv2.imshow("Camera Preview", frame)
    quit_requested = cv2.waitKey(1) & 0xFF == ord("q")
    return direction, quit_requested

class GameObject:
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.type = type

class Log(GameObject):
    def __init__(self, x, y, direction):
        super().__init__(x, y, 'L')
        self.direction = direction # 1 for down, -1 for up
        self.timer = 0

class Fox(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 'F')
        self.timer = 0

def find_start_pos(level_map):
    for y, row in enumerate(level_map):
        for x, char in enumerate(row):
            if char == 'P':
                return x, y
    return 1, 1

def run_game(level_index=0, cap=None, detector=None):
    pygame.init()
    current_level = [list(row) for row in LEVELS[level_index]]
    map_width = len(current_level[0])
    map_height = len(current_level)
    
    tile_size = 64
    width = map_width * tile_size
    height = map_height * tile_size
    
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(f"Rabbit Adventure - Level {level_index + 1}")
    
    textures = load_textures_with_size(tile_size)
    player_textures = create_player_textures(textures)
    
    player_x, player_y = find_start_pos(current_level)
    current_level[player_y][player_x] = '0' # Clear start pos from map
    
    # Initialize level specific objects
    logs = []
    if level_index == 1:
        # Add logs to the river (columns with 'W')
        for x in range(map_width):
            if current_level[1][x] == 'W':
                direction = 1 if x % 2 == 0 else -1
                for y in range(1, map_height - 1, 3):
                    logs.append(Log(x, y, direction))
    
    foxes = []
    if level_index == 2:
        # Add a fox
        foxes.append(Fox(map_width - 2, map_height - 2))
        # Add some carrots for level 3
        current_level[1][map_width-2] = 'C'
        current_level[map_height-2][1] = 'C'

    clock = pygame.time.Clock()
    running = True
    facing_direction = "right"
    moves = 0
    coins = sum(row.count("C") for row in current_level)
    game_over = False
    won = False
    gesture_state = {
        "last_move_at": 0,
        "fist_started_at": None,
    }

    def move_player(dx, dy, new_facing_direction):
        nonlocal player_x, player_y, facing_direction, moves, coins, game_over, won, running

        facing_direction = new_facing_direction
        new_x, new_y = player_x + dx, player_y + dy
        if 0 <= new_x < map_width and 0 <= new_y < map_height:
            target = current_level[new_y][new_x]

            # Check for logs in Level 2
            on_log = False
            for log in logs:
                if log.x == new_x and log.y == new_y:
                    on_log = True
                    break

            if target == '1' or target == 'R': # Wall or Rock
                return
            if target == 'W' and not on_log:
                game_over = True # Drowned
                return

            player_x, player_y = new_x, new_y
            moves += 1
            if target == 'C':
                current_level[player_y][player_x] = '0'
                coins -= 1
            elif target == 'E':
                if coins == 0:
                    won = True
                    running = False

    while running:
        dt = clock.tick(10) # 10 FPS for simple movement
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "quit"
            
            if not game_over and event.type == pygame.KEYDOWN:
                dx, dy = 0, 0
                new_facing_direction = facing_direction
                if event.key in [pygame.K_UP, pygame.K_w]: dy = -1; new_facing_direction = "up"
                elif event.key in [pygame.K_DOWN, pygame.K_s]: dy = 1; new_facing_direction = "down"
                elif event.key in [pygame.K_LEFT, pygame.K_a]: dx = -1; new_facing_direction = "left"
                elif event.key in [pygame.K_RIGHT, pygame.K_d]: dx = 1; new_facing_direction = "right"
                
                if dx != 0 or dy != 0:
                    move_player(dx, dy, new_facing_direction)

        if cap is not None and detector is not None:
            gesture_direction, camera_quit = process_camera_frame(cap, detector, gesture_state)
            if camera_quit:
                return "quit"
            if not game_over and gesture_direction == "up":
                move_player(0, -1, "up")
            elif not game_over and gesture_direction == "down":
                move_player(0, 1, "down")
            elif not game_over and gesture_direction == "left":
                move_player(-1, 0, "left")
            elif not game_over and gesture_direction == "right":
                move_player(1, 0, "right")
        
        # Update Logs
        if level_index == 1:
            on_any_log = False
            for log in logs:
                log.timer += 1
                if log.timer >= 5: # Move every 5 frames
                    log.timer = 0
                    # If player is on this log, move player too
                    if player_x == log.x and player_y == log.y:
                        player_y += log.direction
                    
                    log.y += log.direction
                    # Wrap around
                    if log.y >= map_height - 1: log.y = 1
                    elif log.y <= 0: log.y = map_height - 2
                
                if player_x == log.x and player_y == log.y:
                    on_any_log = True
            
            # Check if player fell in water
            if current_level[player_y][player_x] == 'W' and not on_any_log:
                game_over = True
            # Check if log took player out of bounds
            if player_y <= 0 or player_y >= map_height - 1:
                game_over = True

        # Update Foxes
        if level_index == 2:
            for fox in foxes:
                fox.timer += 1
                if fox.timer >= 8: # Fox moves slower than rabbit
                    fox.timer = 0
                    # Simple AI: move towards player
                    fdx = 1 if player_x > fox.x else -1 if player_x < fox.x else 0
                    fdy = 1 if player_y > fox.y else -1 if player_y < fox.y else 0
                    
                    # Try moving horizontally first
                    if fdx != 0 and current_level[fox.y][fox.x + fdx] not in ['1', 'R', 'E']:
                        fox.x += fdx
                    elif fdy != 0 and current_level[fox.y + fdy][fox.x] not in ['1', 'R', 'E']:
                        fox.y += fdy
                
                if fox.x == player_x and fox.y == player_y:
                    game_over = True

        # Draw
        screen.fill((0, 0, 0))
        # Draw base map
        for y, row in enumerate(current_level):
            for x, char in enumerate(row):
                screen.blit(textures['0'], (x * tile_size, y * tile_size)) # Grass background
                if char != '0':
                    screen.blit(textures.get(char, textures['0']), (x * tile_size, y * tile_size))
        
        # Draw logs
        for log in logs:
            screen.blit(textures['L'], (log.x * tile_size, log.y * tile_size))
            
        # Draw foxes
        for fox in foxes:
            screen.blit(textures['F'], (fox.x * tile_size, fox.y * tile_size))
            
        # Draw player
        screen.blit(player_textures[facing_direction], (player_x * tile_size, player_y * tile_size))
        
        if game_over:
            overlay = pygame.Surface((width, height))
            overlay.set_alpha(180)
            overlay.fill((50, 50, 50))
            screen.blit(overlay, (0, 0))
            
            # Create box for text
            box_width = 600
            box_height = 200
            box_x = width//2 - box_width//2
            box_y = height//2 - box_height//2
            
            # Draw box shadow
            shadow_rect = pygame.Rect(box_x + 5, box_y + 5, box_width, box_height)
            pygame.draw.rect(screen, (20, 20, 20), shadow_rect, border_radius=15)
            
            # Draw box background
            box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
            pygame.draw.rect(screen, (139, 0, 0), box_rect, border_radius=15)
            
            # Draw box border
            pygame.draw.rect(screen, (255, 100, 100), box_rect, 5, border_radius=15)
            
            # Render text
            font_title = pygame.font.SysFont("Arial", 54, bold=True)
            font_sub = pygame.font.SysFont("Arial", 28)
            
            text_title = font_title.render("Game Over!", True, (255, 255, 255))
            text_sub = font_sub.render("Press R to Restart", True, (255, 200, 200))
            
            # Center text in box
            screen.blit(text_title, (width//2 - text_title.get_width()//2, box_y + 50))
            screen.blit(text_sub, (width//2 - text_sub.get_width()//2, box_y + 120))
            
            pygame.display.flip()
            
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: return "quit"
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            return run_game(level_index, cap, detector)
                        if event.key == pygame.K_ESCAPE:
                            return "menu"

        pygame.display.flip()

    if won:
        if level_index + 1 < len(LEVELS):
            return run_game(level_index + 1, cap, detector)
        else:
            # Game Complete - Beautiful Win Screen
            # Create gradient background
            for y in range(height):
                color_value = int(144 + (200 - 144) * (y / height))
                pygame.draw.line(screen, (100, color_value, 100), (0, y), (width, y))
            
            # Create celebration box
            box_width = 500
            box_height = 250
            box_x = width//2 - box_width//2
            box_y = height//2 - box_height//2
            
            # Draw box shadow
            shadow_rect = pygame.Rect(box_x + 8, box_y + 8, box_width, box_height)
            pygame.draw.rect(screen, (30, 80, 30), shadow_rect, border_radius=20)
            
            # Draw box background with gradient effect
            box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
            pygame.draw.rect(screen, (255, 215, 0), box_rect, border_radius=20)
            
            # Inner box for contrast
            inner_rect = pygame.Rect(box_x + 10, box_y + 10, box_width - 20, box_height - 20)
            pygame.draw.rect(screen, (255, 255, 150), inner_rect, border_radius=15)
            
            # Draw decorative border
            pygame.draw.rect(screen, (0, 128, 0), box_rect, 8, border_radius=20)
            pygame.draw.rect(screen, (255, 215, 0), box_rect, 4, border_radius=20)
            
            # Render victory text
            font_title = pygame.font.SysFont("Arial", 72, bold=True)
            font_sub = pygame.font.SysFont("Arial", 36)
            font_detail = pygame.font.SysFont("Arial", 24)
            
            text_title = font_title.render("YOU WIN!", True, (0, 100, 0))
            text_sub = font_sub.render("Congratulations!", True, (34, 139, 34))
            # text_detail = font_detail.render("All levels completed!", True, (50, 150, 50))
            
            # Center text in box
            screen.blit(text_title, (width//2 - text_title.get_width()//2, box_y + 60))
            screen.blit(text_sub, (width//2 - text_sub.get_width()//2, box_y + 150))
            # screen.blit(text_detail, (width//2 - text_detail.get_width()//2, box_y + 210))
            
            pygame.display.flip()
            pygame.time.wait(3000)
            return "menu"

def select_map(screen):
    # For this version, we start from level 1
    return "start"
