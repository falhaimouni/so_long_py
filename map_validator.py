"""Map validation functions."""


def is_map_rectangular(game_map):
    """Check if the map is rectangular (all rows have the same length)."""
    if not game_map or len(game_map) == 0:
        return False
    
    if len(game_map) == 1:
        return True
    
    width = len(game_map[0])
    for row in game_map:
        if len(row) != width:
            return False
    
    return True


def is_map_surrounded_by_walls(game_map):
    """Check if the map is completely surrounded by walls (character '1')."""
    if not game_map or len(game_map) == 0:
        return False
    
    # First check if rectangular - if not, can't check walls safely
    if not is_map_rectangular(game_map):
        return False
    
    height = len(game_map)
    width = len(game_map[0]) if game_map else 0
    
    if width == 0 or height == 0:
        return False
    
    # Check top and bottom borders
    for x in range(width):
        if x >= len(game_map[0]) or x >= len(game_map[height - 1]):
            return False
        if game_map[0][x] != "1" or game_map[height - 1][x] != "1":
            return False
    
    # Check left and right borders
    for y in range(height):
        if len(game_map[y]) != width:
            return False
        if game_map[y][0] != "1" or game_map[y][width - 1] != "1":
            return False
    
    return True


def validate_map_characters(game_map):
    """Check if map contains only valid characters and has exactly 1 P, 1 E, and at least 1 C."""
    valid_chars = {"1", "0", "E", "P", "C", "W", "L", "F", "R"}  # Added W, L, F, R for special levels
    coin_count = 0
    player_count = 0
    exit_count = 0
    
    for row in game_map:
        for cell in row:
            if cell not in valid_chars:
                return False, f"Invalid character found: '{cell}'"
            if cell == "C":
                coin_count += 1
            elif cell == "P":
                player_count += 1
            elif cell == "E":
                exit_count += 1
    
    if player_count == 0:
        return False, "Map must contain exactly one starting position (P)"
    if player_count > 1:
        return False, f"Map contains duplicate starting positions (P): found {player_count}"
    
    if exit_count == 0:
        return False, "Map must contain exactly one exit (E)"
    if exit_count > 1:
        return False, f"Map contains duplicate exits (E): found {exit_count}"
    
    if coin_count == 0:
        return False, "Map must contain at least one collectible (C)"
    
    return True, f"Map is valid with {coin_count} collectible(s)"


def has_valid_path(game_map, start_x, start_y, targets):
    """Check if there's a valid path from start position to all targets using BFS."""
    if not targets:
        return True
    
    height = len(game_map)
    width = len(game_map[0])
    
    # BFS to find all reachable positions
    queue = [(start_x, start_y)]
    visited = set()
    visited.add((start_x, start_y))
    found_targets = set()
    
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # down, up, right, left
    
    while queue:
        x, y = queue.pop(0)
        
        # Check if current position is a target
        if (x, y) in targets:
            found_targets.add((x, y))
            # If we found all targets, we can return early
            if len(found_targets) == len(targets):
                return True
        
        # Explore neighbors
        for dx, dy in directions:
            new_x, new_y = x + dx, y + dy
            
            # Check bounds
            if new_x < 0 or new_x >= width or new_y < 0 or new_y >= height:
                continue
            
            # Check if already visited
            if (new_x, new_y) in visited:
                continue
            
            # Check if it's a walkable tile (not a wall)
            cell = game_map[new_y][new_x]
            if cell != "1":  # Can walk on floor, collectibles, exit, or player position
                visited.add((new_x, new_y))
                queue.append((new_x, new_y))
    
    # Check if we found all targets
    return len(found_targets) == len(targets)


def validate_map(game_map):
    """Validate the entire map and return (is_valid, error_message)."""
    # Check if map is rectangular - must be first!
    if not is_map_rectangular(game_map):
        return False, "Map must be rectangular (all rows must have the same length)"
    
    # Validate map characters
    is_valid, message = validate_map_characters(game_map)
    if not is_valid:
        return False, message
    
    # Check if map is surrounded by walls
    if not is_map_surrounded_by_walls(game_map):
        return False, "Map must be surrounded by walls (character '1')"
    
    return True, "Map is valid"

