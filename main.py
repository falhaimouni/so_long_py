"""Entry point for Rabbit Adventure's booth presentation."""
import cv2
import pygame
from game import run_game
from hand_tracking import HandTracker
from ui import create_display, title_screen


def main():
    tracker = None
    pygame.init()
    try:
        screen = create_display()
        while title_screen(screen):
            if tracker is None:
                tracker = HandTracker().start()
            outcome = run_game(0, tracker)
            if outcome == 'quit':
                break
            screen = pygame.display.get_surface()
    finally:
        if tracker is not None:
            tracker.close()
        cv2.destroyAllWindows()
        pygame.quit()


if __name__ == '__main__':
    main()
