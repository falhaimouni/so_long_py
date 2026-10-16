"""Exercise navigation across the booth screens without a camera or display."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
from unittest.mock import patch
import pygame
import ui
import game


class PresentationTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.screen = ui.create_display()

    def tearDown(self):
        pygame.quit()

    def test_instructions_then_start(self):
        events = iter([[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h)],
                       [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]])
        with patch('pygame.event.get', side_effect=lambda: next(events)):
            self.assertTrue(ui.title_screen(self.screen))

    def test_result_actions_and_quit(self):
        for kind, key, expected in [('pause', pygame.K_p, 'resume'),
                                    ('lost', pygame.K_r, 'restart'),
                                    ('next', pygame.K_RETURN, 'next'),
                                    ('complete', pygame.K_RETURN, 'again'),
                                    ('complete', pygame.K_m, 'menu'),
                                    ('complete', pygame.K_q, 'quit')]:
            with self.subTest(kind=kind, action=expected):
                with patch('pygame.event.get', return_value=[pygame.event.Event(pygame.KEYDOWN, key=key)]):
                    self.assertEqual(ui.modal(self.screen, kind, 'A forest adventure.', 'Follow the trail.'), expected)

    def test_pause_returns_to_title(self):
        with patch('game.pygame.event.get', return_value=[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p)]), \
             patch('game.modal', return_value='menu') as dialog:
            self.assertEqual(game.run_game(), 'menu')
            self.assertEqual(dialog.call_args.args[1], 'pause')

    def test_replay_starts_from_first_level(self):
        with patch('game._run_level', side_effect=['again', 'quit']) as level:
            self.assertEqual(game.run_game(5), 'quit')
            self.assertEqual([call.args[0] for call in level.call_args_list], [5, 0])


if __name__ == '__main__':
    unittest.main()
