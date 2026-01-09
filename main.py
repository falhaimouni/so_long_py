"""Main entry point for Rabbit Adventure."""

import os
import pygame
from game import run_game

def show_intro(screen):
    """Show the game logo and wait for a key press."""
    logo_path = "textures/game_logo.png"
    try:
        logo = pygame.image.load(logo_path)
        # Scale logo to fit screen
        logo = pygame.transform.scale(logo, (600, 600))
        
        screen.fill((144, 238, 144)) # Grass green background
        screen.blit(logo, (screen.get_width()//2 - 300, screen.get_height()//2 - 300))
        
        font = pygame.font.SysFont("Arial", 32)
        text = font.render("Press any key to start the adventure!", True, (0, 100, 0))
        screen.blit(text, (screen.get_width()//2 - text.get_width()//2, screen.get_height() - 100))
        
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
        return True
    except Exception as e:
        print(f"Could not load logo: {e}")
        return True

def main():
    """Main function to start the game."""
    
    pygame.init()
    screen = pygame.display.set_mode((960, 704)) # Matches 15x11 tiles of 64px
    pygame.display.set_caption("Rabbit Adventure")

    if show_intro(screen):
        run_game(0) # Start from Level 1
    
    pygame.quit()

if __name__ == "__main__":
    main()
