"""UI rendering functions."""

import pygame
from config import (BG_COLOR, BUTTON_COLOR, BUTTON_HOVER, BUTTON_BORDER,
                   TEXT_COLOR, TITLE_COLOR, SUBTITLE_COLOR, SHADOW_COLOR)


def draw_buttons(screen, buttons, mouse_pos):
    """Draw the map selection screen with beautiful UI."""
    screen.fill(BG_COLOR)
    
    # Draw gradient background effect
    for y in range(screen.get_height()):
        color_factor = int(30 + (y / screen.get_height()) * 10)
        pygame.draw.line(screen, (color_factor, color_factor, color_factor + 10), 
                        (0, y), (screen.get_width(), y))
    
    # Draw title with shadow
    title_font = pygame.font.Font(None, 72)
    title_text = title_font.render("SO LONG", True, SHADOW_COLOR)
    title_rect = title_text.get_rect(center=(screen.get_width() // 2 + 3, 53))
    screen.blit(title_text, title_rect)
    
    title_text = title_font.render("SO LONG", True, TITLE_COLOR)
    title_rect = title_text.get_rect(center=(screen.get_width() // 2, 50))
    screen.blit(title_text, title_rect)
    
    # Draw subtitle
    subtitle_font = pygame.font.Font(None, 32)
    subtitle_text = subtitle_font.render("Select a Map", True, SUBTITLE_COLOR)
    subtitle_rect = subtitle_text.get_rect(center=(screen.get_width() // 2, 100))
    screen.blit(subtitle_text, subtitle_rect)
    
    # Draw decorative line
    pygame.draw.line(screen, BUTTON_BORDER, (150, 120), (screen.get_width() - 150, 120), 2)
    
    # Draw buttons with enhanced styling
    button_font = pygame.font.Font(None, 36)
    for i, (rect, text) in enumerate(buttons):
        is_hovered = rect.collidepoint(mouse_pos)
        
        # Button shadow
        shadow_rect = rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pygame.draw.rect(screen, SHADOW_COLOR, shadow_rect, border_radius=8)
        
        # Button background with gradient effect
        color = BUTTON_HOVER if is_hovered else BUTTON_COLOR
        
        # Main button rectangle with rounded corners effect
        pygame.draw.rect(screen, color, rect, border_radius=8)
        
        # Button border
        border_color = BUTTON_BORDER if is_hovered else (color[0] + 30, color[1] + 30, color[2] + 30)
        pygame.draw.rect(screen, border_color, rect, width=2, border_radius=8)
        
        # Button text with shadow
        text_shadow = button_font.render(text, True, SHADOW_COLOR)
        text_shadow_rect = text_shadow.get_rect(center=(rect.centerx + 2, rect.centery + 2))
        screen.blit(text_shadow, text_shadow_rect)
        
        text_surf = button_font.render(text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)
        
        # Draw icon/indicator for hovered button
        if is_hovered:
            indicator_size = 8
            indicator_x = rect.left + 15
            indicator_y = rect.centery
            pygame.draw.circle(screen, TITLE_COLOR, (indicator_x, indicator_y), indicator_size)
    
    # Draw footer
    footer_font = pygame.font.Font(None, 24)
    footer_text = footer_font.render("Use mouse to select • ESC to exit", True, SUBTITLE_COLOR)
    footer_rect = footer_text.get_rect(center=(screen.get_width() // 2, screen.get_height() - 30))
    screen.blit(footer_text, footer_rect)
    
    pygame.display.flip()


def draw_game(screen, game_map, textures, player_textures, player_x, player_y, 
              facing_direction, moves, tile_size):
    """Draw the game map and player."""
    screen.fill((0, 0, 0))
    
    # Draw map
    for y, row in enumerate(game_map):
        for x, cell in enumerate(row):
            pos = (x * tile_size, y * tile_size)
            # Always draw floor first (background)
            screen.blit(textures["0"], pos)
            # Draw the cell texture (wall, coin, or exit)
            if cell in ["1", "C", "E"]:
                screen.blit(textures[cell], pos)
            # Draw player on top if at this position
            if (x, y) == (player_x, player_y):
                player_texture = player_textures[facing_direction]
                screen.blit(player_texture, pos)
    
    # Draw moves counter on screen (scale font size based on tile size)
    font_size = max(24, int(tile_size * 0.3))
    font = pygame.font.Font(None, font_size)
    moves_text = font.render(f"Moves: {moves}", True, TEXT_COLOR)
    screen.blit(moves_text, (10, 10))
    
    pygame.display.flip()

