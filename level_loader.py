"""Load and validate the game's level file."""
from pathlib import Path
from map_validator import validate_map


def get_levels():
    content = Path(__file__).with_name('levels.txt').read_text()
    levels = [block.splitlines() for block in content.strip().split('\n---\n') if block.strip()]
    if not levels:
        raise ValueError('levels.txt contains no levels')
    for index, level in enumerate(levels, 1):
        valid, message = validate_map(level)
        if not valid:
            raise ValueError(f'Level {index}: {message}')
    return levels
