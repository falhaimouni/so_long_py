"""Game logic and main game loop for Rabbit Adventure."""

import pygame

from config import (TARGET_FPS, MOVE_INTERVAL_MS, ANIMATION_MS,
                    LOG_INTERVAL_MS, FOX_INTERVAL_MS, PORTAL_FOX_INTERVAL_MS, PORTAL_FOX_GRACE_MS)
from hand_tracking import now_ms
from motion import AnimatedPosition, MoveRepeater
from texture_loader import load_textures_with_size, create_player_textures
from level_loader import get_levels
from level_mechanics import LevelMechanics, PuzzleState, LEVEL_GUIDES, next_fox_position
from effects import Feedback
from hazards import HazardField
from ui import create_display, draw_hud, draw_camera, modal, fullscreen, panel, render_scale, point

LEVELS = get_levels()
DIRECTIONS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
KEY_DIRECTIONS = {
    pygame.K_UP: "up", pygame.K_w: "up",
    pygame.K_DOWN: "down", pygame.K_s: "down",
    pygame.K_LEFT: "left", pygame.K_a: "left",
    pygame.K_RIGHT: "right", pygame.K_d: "right",
}

class GameObject:
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.type = type
        self.animation = AnimatedPosition(x, y, ANIMATION_MS)

class Log(GameObject):
    def __init__(self, x, y, direction):
        super().__init__(x, y, 'L')
        self.direction = direction # 1 for down, -1 for up
        self.timer = 0

class Fox(GameObject):
    def __init__(self, x, y, interval_ms=FOX_INTERVAL_MS, delay_ms=0):
        super().__init__(x, y, 'F')
        self.facing_direction = "left"
        self.interval_ms = interval_ms
        self.timer = -delay_ms

def find_start_pos(level_map):
    for y, row in enumerate(level_map):
        for x, char in enumerate(row):
            if char == 'P':
                return x, y
    return 1, 1

def run_game(level_index=0, tracker=None):
    """Reuse the same camera across levels and restarts without recursive loops."""
    while True:
        outcome = _run_level(level_index, tracker)
        if outcome == "restart":
            continue
        if outcome == "again":
            level_index = 0
            continue
        if outcome == "next":
            level_index += 1
            continue
        return outcome


def _run_level(level_index, tracker):
    pygame.init()
    current_level = [list(row) for row in LEVELS[level_index]]
    map_width = len(current_level[0])
    map_height = len(current_level)
    
    screen = create_display()
    tile_size = max(1, int(64 * render_scale()))
    width = map_width * tile_size
    height = map_height * tile_size
    
    board = pygame.Surface((width, height)).convert()
    title, hint = LEVEL_GUIDES[level_index] if level_index < len(LEVEL_GUIDES) else (
        "Adventure", "Collect every carrot and reach the burrow.")
    pygame.display.set_caption(f"Rabbit Adventure - Level {level_index + 1}: {title}")
    
    textures = load_textures_with_size(tile_size)
    player_textures = create_player_textures(textures)
    # The fox artwork faces left; cache its mirror once per level.
    fox_textures = {"left": textures["F"],
                    "right": pygame.transform.flip(textures["F"], True, False)}
    
    player_x, player_y = find_start_pos(current_level)
    current_level[player_y][player_x] = '0' # Clear start pos from map
    mechanics = LevelMechanics(current_level)
    puzzle_state = PuzzleState()
    
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
    for y, row in enumerate(current_level):
        for x, char in enumerate(row):
            if char == 'F':
                foxes.append(Fox(x, y, PORTAL_FOX_INTERVAL_MS if level_index == 4 else FOX_INTERVAL_MS,
                                 PORTAL_FOX_GRACE_MS if level_index == 4 else 0))
                current_level[y][x] = '0'
    hazards = HazardField(level_index, current_level)

    portal_positions = [(x,y,char) for y,row in enumerate(current_level)
                        for x,char in enumerate(row) if char in 'ABUV']
    switch_positions = [(x,y) for y,row in enumerate(current_level)
                        for x,char in enumerate(row) if char == 'S']
    clock = pygame.time.Clock()
    facing_direction = "right"
    coins = sum(row.count("C") for row in current_level)
    game_over = False
    won = False
    player_animation = AnimatedPosition(player_x, player_y, ANIMATION_MS)
    repeater = MoveRepeater(MOVE_INTERVAL_MS)
    held_keys = []
    initial_coins = coins
    moves = 0
    feedback = Feedback()
    elapsed_ms = 0

    # Cache the map; redraw only tiles changed by carrots, gates, or planks.
    background = pygame.Surface((width, height)).convert()

    def redraw_tile(x, y):
        background.blit(textures['0'], (x * tile_size, y * tile_size))
        char = mechanics.texture_key((x, y), puzzle_state)
        if char != '0':
            background.blit(textures.get(char, textures['0']), (x * tile_size, y * tile_size))

    for y, row in enumerate(current_level):
        for x in range(len(row)):
            redraw_tile(x, y)

    def move_player(dx, dy, new_facing_direction):
        nonlocal player_x, player_y, facing_direction, coins, game_over, won, puzzle_state, moves

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

            if mechanics.fragile.get((new_x, new_y), 0) & puzzle_state.collapsed:
                game_over = True
                return
            if mechanics.blocked((new_x, new_y), puzzle_state):
                return
            if target == 'W' and not on_log:
                game_over = True
                return

            moves += 1
            origin = (player_x, player_y)
            previous_state = puzzle_state
            (player_x, player_y), puzzle_state = mechanics.enter(origin, (new_x, new_y), puzzle_state)
            hazards.arrive((player_x, player_y))
            teleported = (player_x, player_y) != (new_x, new_y)
            player_animation.move_to(player_x, player_y, now, snap=teleported)
            if previous_state.sun_open != puzzle_state.sun_open:
                for gate in mechanics.gates:
                    redraw_tile(*gate)
            if previous_state.collapsed != puzzle_state.collapsed:
                redraw_tile(*origin)
            if hazards.deadly((player_x, player_y)) or any(
                    (fox.x, fox.y) == (player_x, player_y) for fox in foxes):
                game_over = True
                return
            target = current_level[player_y][player_x]
            if target == 'C':
                current_level[player_y][player_x] = '0'
                coins -= 1
                feedback.collect((player_x+.5)*tile_size, (player_y+.5)*tile_size)
                redraw_tile(player_x, player_y)
            elif target == 'E':
                if coins == 0:
                    won = True

    while True:
        dt = clock.tick(TARGET_FPS)
        now = now_ms()
        elapsed_ms += dt
        hazards.advance(dt)
        if not won and hazards.deadly((player_x, player_y)):
            game_over = True
        pressed_direction = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return "quit"
                if event.key == pygame.K_r:
                    return "restart"
                if event.key == pygame.K_m:
                    Feedback.muted = not Feedback.muted
                if event.key == pygame.K_F11:
                    fullscreen()
                if event.key == pygame.K_p:
                    action = modal(screen, 'pause', 'A moment in the woods.',
                                   'Your adventure is waiting. Take your time, then follow the trail.',
                                   'ENTER / P  Resume     M  Title     Q  Exit', tracker)
                    if action != 'resume':
                        return action
                    held_keys.clear()
                    repeater = MoveRepeater(MOVE_INTERVAL_MS)
                    clock.tick(TARGET_FPS)
                    now = now_ms()
                if event.key in KEY_DIRECTIONS:
                    if event.key not in held_keys:
                        held_keys.append(event.key)
                        pressed_direction = KEY_DIRECTIONS[event.key]
            elif event.type == pygame.KEYUP and event.key in held_keys:
                held_keys.remove(event.key)
            elif event.type == pygame.WINDOWFOCUSLOST:
                held_keys.clear()
                pressed_direction = None
                repeater.poll(None, now)

        screen = pygame.display.get_surface()
        new_tile_size = max(1, int(64 * render_scale()))
        if new_tile_size != tile_size:
            tile_size = new_tile_size
            width, height = map_width * tile_size, map_height * tile_size
            board = pygame.Surface((width, height)).convert()
            background = pygame.Surface((width, height)).convert()
            textures = load_textures_with_size(tile_size)
            player_textures = create_player_textures(textures)
            fox_textures = {"left": textures["F"],
                            "right": pygame.transform.flip(textures["F"], True, False)}
            for y, row in enumerate(current_level):
                for x in range(len(row)):
                    redraw_tile(x, y)

        # Reconcile held keys with actual state (e.g. a release while unfocused).
        keys = pygame.key.get_pressed()
        held_keys[:] = [key for key in held_keys if keys[key]]
        for key in KEY_DIRECTIONS:
            if keys[key] and key not in held_keys:
                held_keys.append(key)
        keyboard_direction = pressed_direction or (KEY_DIRECTIONS[held_keys[-1]] if held_keys else None)
        state = tracker.snapshot(now) if tracker is not None else None
        direction = keyboard_direction or (state.direction if state is not None else None)
        step = repeater.poll(direction, now)
        if step is not None and not game_over and not won:
            move_player(*DIRECTIONS[step], step)
        if won and now - player_animation.started_at >= ANIMATION_MS:
            break

        # Update Logs
        if level_index == 1 and not game_over and not won:
            on_any_log = False
            for log in logs:
                log.timer += dt
                while log.timer >= LOG_INTERVAL_MS:
                    log.timer -= LOG_INTERVAL_MS
                    # If player is on this log, move player too
                    if player_x == log.x and player_y == log.y:
                        player_y += log.direction
                        player_animation.move_to(player_x, player_y, now)
                    
                    log.y += log.direction
                    # Wrap around
                    wrapped = False
                    if log.y >= map_height - 1:
                        log.y = 1
                        wrapped = True
                    elif log.y <= 0:
                        log.y = map_height - 2
                        wrapped = True
                    log.animation.move_to(log.x, log.y, now, snap=wrapped)
                
                if player_x == log.x and player_y == log.y:
                    on_any_log = True
            
            # Check if player fell in water
            if current_level[player_y][player_x] == 'W' and not on_any_log:
                game_over = True
            # Check if log took player out of bounds
            if player_y <= 0 or player_y >= map_height - 1:
                game_over = True

        # Check contact before a fox moves, so stepping onto one is always fatal.
        if foxes and not game_over and not won:
            for fox in foxes:
                if (fox.x, fox.y) == (player_x, player_y):
                    game_over = True
                    break
                fox.timer += dt
                while fox.timer >= fox.interval_ms:
                    fox.timer -= fox.interval_ms
                    previous = (fox.x, fox.y)
                    fox.x, fox.y = next_fox_position(
                        current_level, previous, (player_x, player_y), mechanics,
                        puzzle_state, use_portals=level_index == 4)
                    teleported = abs(fox.x - previous[0]) + abs(fox.y - previous[1]) > 1
                    if not teleported and fox.x != previous[0]:
                        fox.facing_direction = "right" if fox.x > previous[0] else "left"
                    fox.animation.move_to(fox.x, fox.y, now, snap=teleported)
                    if (fox.x, fox.y) == (player_x, player_y):
                        game_over = True
                        break
                if game_over:
                    break

        # Collision uses tile coordinates; drawing interpolates between them.
        board.blit(background, (0, 0))
        portal_frame = int(hazards.elapsed / 90) % 16
        for x, y, char in portal_positions:
            board.blit(textures['0'], (x*tile_size,y*tile_size))
            board.blit(textures[f'{char}_{portal_frame}'], (x*tile_size,y*tile_size))
        for x,y in switch_positions:
            board.blit(textures['0'], (x*tile_size,y*tile_size))
            board.blit(textures['S_on' if puzzle_state.sun_open else 'S'], (x*tile_size,y*tile_size))
        hazards.draw(board, textures, tile_size, mechanics, puzzle_state)
        for obj in (*logs, *foxes):
            draw_x, draw_y = obj.animation.position(now)
            sprite = fox_textures[obj.facing_direction] if isinstance(obj, Fox) else textures[obj.type]
            board.blit(sprite, (round(draw_x * tile_size), round(draw_y * tile_size)))
        draw_x, draw_y = player_animation.position(now)
        board.blit(player_textures[facing_direction],
                    (round(draw_x * tile_size), round(draw_y * tile_size)))

        feedback.draw(board, dt)
        if coins == 0:
            for y, row in enumerate(current_level):
                for x, char in enumerate(row):
                    if char == 'E':
                        pygame.draw.circle(board, (213, 234, 156),
                                           (round((x+.5)*tile_size), round((y+.5)*tile_size)),
                                           tile_size//2-3, 2)
        danger_status = hazards.status((player_x, player_y))
        if level_index == 4:
            wake_in = max(0, PORTAL_FOX_GRACE_MS + PORTAL_FOX_INTERVAL_MS - hazards.elapsed)
            danger_status = (f"Fox wakes in {wake_in / 1000:.1f}s" if wake_in else
                             "The fox can follow you through portals. Keep moving.")
        gate_status = ''
        if mechanics.gates:
            gate_status = 'Sun gates open / Moon gates closed' if puzzle_state.sun_open else 'Moon gates open / Sun gates closed'
        draw_hud(screen, level_index, len(LEVELS), title, hint, coins, initial_coins,
                 danger_status, gate_status)
        panel(screen, pygame.Rect(36, 94, 968, 712))
        screen.blit(board, point((40, 98)))
        if tracker is not None:
            draw_camera(screen, tracker)

        if game_over:
            feedback.play('lost')
            return modal(screen, 'lost', 'Every trail takes practice.',
                         'The forest caught you this time. Try a new route, watch the hazards, and keep your harvest safe.',
                         f'{initial_coins-coins} / {initial_coins} carrots   /   {moves} steps   /   {elapsed_ms/1000:.1f}s', tracker)

        pygame.display.flip()

    if won:
        feedback.play('win')
        final = level_index + 1 == len(LEVELS)
        return modal(screen, 'complete' if final else 'next',
                     'Welcome home, little hero.' if final else 'A little closer to home.',
                     'Every carrot gathered. Every trail conquered. The woodland is yours. Pass the adventure to the next explorer.' if final else
                     f'{title} complete. Your harvest is safe. A new corner of the forest awaits.',
                     f'{initial_coins} / {initial_coins} carrots   /   {moves} steps   /   {elapsed_ms/1000:.1f}s', tracker)
