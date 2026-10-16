"""Small, dependency-free audio cues and collection particles."""
from array import array
import math
import random
import pygame


class Feedback:
    muted = False

    def __init__(self):
        self.particles = []
        self.sounds = {}
        settings = pygame.mixer.get_init()
        if settings and settings[1] == -16:
            rate, _, channels = settings
            for name, notes in {'collect': (659, 880), 'win': (523, 659, 784, 1047),
                                'lost': (330, 262, 196)}.items():
                samples = array('h')
                duration = .095
                for pitch in notes:
                    count = int(rate * duration)
                    for i in range(count):
                        t = i / rate
                        envelope = min(1, i / (rate*.008)) * (1-i/count)**2
                        value = int(2600 * envelope * math.sin(2*math.pi*pitch*t))
                        samples.extend([value] * channels)
                self.sounds[name] = pygame.mixer.Sound(buffer=samples)

    def play(self, name):
        if not self.muted and name in self.sounds:
            self.sounds[name].play()

    def collect(self, x, y):
        self.play('collect')
        for _ in range(18):
            angle = random.random()*math.tau
            speed = random.uniform(15, 60)
            self.particles.append([x, y, math.cos(angle)*speed, math.sin(angle)*speed-15, .65])

    def draw(self, surface, dt):
        alive = []
        for p in self.particles:
            p[4] -= dt/1000
            if p[4] <= 0:
                continue
            p[0] += p[2]*dt/1000
            p[1] += p[3]*dt/1000
            pygame.draw.circle(surface, (239, 201, 115), (round(p[0]), round(p[1])), max(1, round(p[4]*5)))
            alive.append(p)
        self.particles = alive
