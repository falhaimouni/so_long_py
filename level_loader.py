"""Level loader with validation."""

from map_validator import validate_map


def load_levels_from_file(filepath):
    """Load all levels from a file and validate them.
    
    Levels are separated by '---' on a line by itself.
    Returns a list of validated level maps.
    """
    levels = []
    current_level = []
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.rstrip('\n')  # Remove newline but keep other whitespace
                
                if line == '---':
                    # End of current level
                    if current_level:
                        # Convert to list of lists
                        level_map = [list(row) for row in current_level]
                        
                        # Validate the level
                        is_valid, message = validate_map(level_map)
                        if is_valid:
                            levels.append(current_level)
                            print(f"Level {len(levels)} loaded successfully: {message}")
                        else:
                            print(f"WARNING: Level {len(levels) + 1} validation failed: {message}")
                            print("This level will be skipped.")
                        
                        current_level = []
                else:
                    current_level.append(line)
            
            # Don't forget the last level if file doesn't end with ---
            if current_level:
                level_map = [list(row) for row in current_level]
                is_valid, message = validate_map(level_map)
                if is_valid:
                    levels.append(current_level)
                    print(f"Level {len(levels)} loaded successfully: {message}")
                else:
                    print(f"WARNING: Level {len(levels) + 1} validation failed: {message}")
                    print("This level will be skipped.")
    
    except FileNotFoundError:
        print(f"ERROR: Could not find levels file: {filepath}")
        return []
    except Exception as e:
        print(f"ERROR: Failed to load levels: {e}")
        return []
    
    if not levels:
        print("ERROR: No valid levels were loaded!")
    
    return levels


def get_levels():
    """Get all game levels from the levels file."""
    import os
    
    # Try to find levels.txt in current directory or parent directory
    possible_paths = [
        'levels.txt',
        os.path.join(os.path.dirname(__file__), 'levels.txt'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            levels = load_levels_from_file(path)
            if levels:
                return levels
    
    # Fallback to hardcoded levels if file not found
    print("WARNING: Could not load levels from file, using fallback levels")
    return [
        [
            "111111111111111",
            "1P0000010000001",
            "101110010111001",
            "100010000001001",
            "110011111101011",
            "1000000C0000001",
            "101111111111101",
            "100000000000001",
            "101111111111101",
            "1000000C00000E1",
            "111111111111111"
        ],
        [
            "111111111111111",
            "1P0000WW00000C1",
            "100000WW0000001",
            "100000WW0000001",
            "100000WW00000C1",
            "100000WW0000001",
            "100000WW0000001",
            "100000WW0000001",
            "100000WW0000001",
            "1C0000WW00000E1",
            "111111111111111"
        ],
        [
            "111111111111111",
            "1P0000000000001",
            "101111111111101",
            "101000000000001",
            "101011111110101",
            "101010000010101",
            "1010101E1010101",
            "101010000010101",
            "100011101110101",
            "101000000000101",
            "111111111111111"
        ]
    ]
