"""Shared booth presentation: title, instructions, HUD and modal screens."""
from functools import lru_cache
from pathlib import Path
import pygame
import math

ROOT = Path(__file__).resolve().parent
SIZE = (1280, 900)
INK = (112, 132, 100)
PANEL = (221, 223, 196)
BORDER = (144, 160, 119)
CREAM = (40, 72, 44)
MUTED = (65, 86, 57)
MINT = (76, 123, 62)
GOLD = (164, 102, 36)

@lru_cache(maxsize=32)
def font(size, serif=False):
    return pygame.font.SysFont('DejaVu Serif' if serif else 'DejaVu Sans', size)


def text(surface, copy, pos, size=18, color=CREAM, serif=False):
    image = font(size, serif).render(str(copy), True, color)
    surface.blit(image, pos)
    return image.get_rect(topleft=pos)


def wrapped(surface, copy, pos, width, size=17, color=MUTED):
    x, y = pos
    line = ''
    for word in copy.split():
        candidate = (line + ' ' + word).strip()
        if font(size).size(candidate)[0] > width and line:
            text(surface, line, (x, y), size, color)
            y += size + 9
            line = word
        else:
            line = candidate
    if line:
        text(surface, line, (x, y), size, color)
        y += size + 9
    return y


def panel(surface, rect, fill=PANEL):
    pygame.draw.rect(surface, fill, rect, border_radius=18)
    pygame.draw.rect(surface, BORDER, rect, 1, border_radius=18)


def button(surface, rect, label, primary=True, hover=False):
    rect = pygame.Rect(rect)
    fill = (92, 145, 76) if primary and hover else MINT if primary else (231, 240, 213) if hover else PANEL
    pygame.draw.rect(surface, fill, rect, border_radius=10)
    if not primary:
        pygame.draw.rect(surface, BORDER, rect, 1, border_radius=10)
    image = font(18).render(label, True, (249, 241, 215) if primary else CREAM)
    surface.blit(image, image.get_rect(center=rect.center))
    return rect


def create_display():
    font.cache_clear()
    current = pygame.display.get_surface()
    if current is not None and current.get_size() == SIZE:
        return current
    flags = pygame.RESIZABLE | pygame.SCALED if pygame.display.get_driver() != 'dummy' else 0
    screen = pygame.display.set_mode(SIZE, flags)
    pygame.display.set_caption('Rabbit Adventure | The Woodland Trials')
    return screen


def fullscreen():
    if pygame.display.get_driver() != 'dummy':
        pygame.display.toggle_fullscreen()


@lru_cache(maxsize=4)
def background_art(filename, size):
    art = pygame.image.load(str(ROOT / 'textures' / 'woodland' / filename)).convert()
    scale = max(size[0] / art.get_width(), size[1] / art.get_height())
    art = pygame.transform.smoothscale(art, (round(art.get_width()*scale), round(art.get_height()*scale)))
    cropped = pygame.Surface(size)
    cropped.blit(art, ((size[0]-art.get_width())//2, (size[1]-art.get_height())//2))
    return cropped


@lru_cache(maxsize=4)
def title_art(size):
    art = background_art('title-day.png', size).copy()
    shade = pygame.Surface(size, pygame.SRCALPHA)
    for x in range(size[0]):
        pygame.draw.line(shade, (226, 224, 193, round(235 * (1-x/size[0])**1.8)), (x, 0), (x, size[1]))
    art.blit(shade, (0, 0))
    return art


def title_screen(screen):
    font.cache_clear()
    clock = pygame.time.Clock()
    instructions = False
    while True:
        screen.blit(title_art(screen.get_size()), (0, 0))
        w, h = screen.get_size()
        sx, sy = w / 1280, h / 900
        # Title remains usable in the original small window used by embedders.
        x, top = round(72*sx), round(120*sy)
        text(screen, 'A HAND-CONTROLLED WOODLAND ADVENTURE', (x, top), 14, MINT)
        text(screen, 'Rabbit', (x-4, top+42), 76 if w >= 1100 else 60, serif=True)
        text(screen, 'Adventure', (x-4, top+130), 76 if w >= 1100 else 60, serif=True)
        text(screen, 'T H E   W O O D L A N D   T R I A L S', (x, top+237), 16, GOLD)
        wrapped(screen, 'Collect the carrots. Find your way home.', (x, top+300), 420, 22, CREAM)
        mouse = pygame.mouse.get_pos()
        play_rect = pygame.Rect(x, h-212, 260, 58)
        help_rect = pygame.Rect(x+276, h-212, 190, 58)
        button(screen, play_rect, 'Begin adventure  >', hover=play_rect.collidepoint(mouse))
        button(screen, help_rect, 'How to play', False, help_rect.collidepoint(mouse))
        text(screen, 'ENTER  Begin     H  Instructions     F11  Fullscreen', (x, h-124), 14, MUTED)
        text(screen, 'SIX FOREST TRIALS  /  HANDS OR KEYS', (x, h-54), 12, MINT)
        text(screen, 'Q  Exit', (w-100, h-54), 13, MUTED)
        if instructions:
            veil = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            veil.fill((31, 51, 35, 155))
            screen.blit(veil, (0, 0))
            r = pygame.Rect((w-720)//2, (h-450)//2, 720, 450)
            panel(screen, r)
            tx, ty = r.x+40, r.y+30
            text(screen, 'YOUR FIELD GUIDE', (tx, ty), 13, GOLD)
            text(screen, 'Find your way home.', (tx, ty+35), 34, serif=True)
            rows = [('01', 'Your goal', 'Collect every carrot, then reach the burrow.'),
                    ('02', 'Move', 'WASD / arrows, or point with one index finger.'),
                    ('03', 'Stop', 'Open your palm or make a fist. P pauses; R retries.')]
            yy = ty+100
            for num, heading, copy in rows:
                text(screen, num, (tx, yy), 19, MINT, True)
                text(screen, heading, (tx+48, yy), 18)
                text(screen, copy, (tx+48, yy+29), 15, MUTED)
                yy += 73
            help_start = pygame.Rect(tx, r.bottom-77, 310, 48)
            button(screen, help_start, 'Enter the forest  >', hover=help_start.collidepoint(mouse))
            text(screen, 'H / ESC  Back', (tx+470, r.bottom-63), 14, MUTED)
        pygame.display.flip()
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return False
                if event.key == pygame.K_F11:
                    fullscreen()
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return True
                elif event.key == pygame.K_h:
                    instructions = not instructions
                elif event.key == pygame.K_ESCAPE:
                    instructions = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if instructions:
                    if help_start.collidepoint(event.pos):
                        return True
                elif play_rect.collidepoint(event.pos):
                    return True
                elif help_rect.collidepoint(event.pos):
                    instructions = True


def draw_hud(screen, level, total, title, hint, coins, initial_coins, danger, gate):
    """Keep the board central, with only a slim header and a short hint."""
    screen.fill(INK)
    panel(screen, pygame.Rect(160, 22, 960, 56))
    text(screen, f'{level+1:02d} / {total:02d}', (184, 40), 15, MUTED)
    text(screen, title, (290, 35), 23, serif=True)
    collected = initial_coins - coins
    text(screen, f'Carrots  {collected} / {initial_coins}', (946, 39), 17, MINT)
    instruction = 'All carrots collected! Head to the burrow.' if coins == 0 else hint
    rendered = font(16).render(instruction, True, (249, 242, 217))
    screen.blit(rendered, rendered.get_rect(center=(640, 824)))
    status = '  /  '.join(part for part in (gate, danger) if part)
    if status:
        rendered = font(13).render(status, True, (250, 215, 151))
        screen.blit(rendered, rendered.get_rect(center=(640, 849)))
    rendered = font(12).render('WASD / arrows or point to move   ·   Palm / fist to stop   ·   P Pause   ·   R Retry   ·   F11 Fullscreen   ·   Q Exit', True, (222, 231, 204))
    screen.blit(rendered, rendered.get_rect(center=(640, 879)))


def draw_happy_ending(screen, stats, elapsed):
    screen.blit(background_art('ending.png', screen.get_size()), (0,0))
    w, h = screen.get_size()
    # Petals drift through the scene; the success screen stays alive until input.
    for i in range(32):
        x = (i*137+math.sin(elapsed*.6+i)*28) % w
        y = (i*83+elapsed*(18+i%5*4)) % h
        tint = ((232, 186, 90), (243, 217, 151), (172, 192, 113))[i%3]
        pygame.draw.ellipse(screen, tint, (round(x),round(y),7+i%3,4+i%2))
    box = pygame.Rect(52, 90, 580, 718)
    glass = pygame.Surface(box.size, pygame.SRCALPHA)
    pygame.draw.rect(glass, (33, 58, 41, 237), glass.get_rect(), border_radius=24)
    pygame.draw.rect(glass, (183, 172, 115, 160), glass.get_rect(), 1, border_radius=24)
    screen.blit(glass, box)
    ivory, gold = (249, 239, 211), (235, 194, 114)
    text(screen, 'THE WOODLAND IS CELEBRATING', (90, 130), 13, gold)
    text(screen, 'Home, sweet', (85, 180), 60, ivory, True)
    text(screen, 'home.', (85, 254), 60, ivory, True)
    text(screen, 'Six trails. One brave little rabbit.', (90, 352), 20, ivory)
    wrapped(screen, 'The harvest is safe, the basket is full, and a cozy burrow is waiting for you.',
            (90, 396), 478, 18, (205, 220, 179))
    # Six earned star medallions replace a plain completion paragraph.
    for i in range(6):
        cx, cy = 119+i*79, 528
        pygame.draw.circle(screen, (96, 116, 67), (cx,cy), 27)
        pygame.draw.circle(screen, gold, (cx,cy), 25, 1)
        points = []
        for j in range(10):
            angle = j*math.pi/5-math.pi/2
            radius = 15 if j%2 == 0 else 7
            points.append((cx+math.cos(angle)*radius,cy+math.sin(angle)*radius))
        pygame.draw.polygon(screen, gold, points)
    text(screen, 'ALL SIX TRIALS COMPLETE', (90, 582), 14, gold)
    text(screen, 'Final trail: '+stats, (90, 624), 13, (205,220,179))
    first = pygame.Rect(90, 690, 240, 56)
    second = pygame.Rect(346, 690, 240, 56)
    mouse = pygame.mouse.get_pos()
    button(screen, first, 'Play again', hover=first.collidepoint(mouse))
    button(screen, second, 'Back to title', False, second.collidepoint(mouse))
    text(screen, 'ENTER  Play again    M  Title    Q  Exit', (90, 770), 12, (205,220,179))
    return first, second


def modal(screen, kind, title, copy, stats='', tracker=None):
    """Return a concrete action. Gameplay is frozen while this loop owns events."""
    frozen = screen.copy()
    veil = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    veil.fill((31, 51, 35, 150))
    frozen.blit(veil, (0, 0))
    clock = pygame.time.Clock()
    pause = kind == 'pause'
    primary_label = {'pause': 'Resume adventure', 'lost': 'Try again', 'next': 'Next trial  >', 'complete': 'Play again'}[kind]
    primary_action = {'pause': 'resume', 'lost': 'restart', 'next': 'next', 'complete': 'again'}[kind]
    w, h = screen.get_size()
    box = pygame.Rect((w-680)//2, (h-430)//2, 680, 430)
    first = pygame.Rect(box.x+48, box.bottom-93, 282, 56)
    second = pygame.Rect(box.x+348, box.bottom-93, 282, 56)
    started_at = pygame.time.get_ticks()
    while True:
        if kind == 'complete':
            first, second = draw_happy_ending(screen, stats, (pygame.time.get_ticks()-started_at)/1000)
        else:
            screen.blit(frozen, (0, 0))
            panel(screen, box)
            text(screen, {'pause': 'TAKE A BREATHER', 'lost': 'THE FOREST HAS ANOTHER CHANCE', 'next': 'TRIAL COMPLETE', 'complete': 'ALL SIX TRIALS COMPLETE'}[kind], (box.x+48, box.y+37), 13, GOLD)
            text(screen, title, (box.x+48, box.y+84), 40, serif=True)
            wrapped(screen, copy, (box.x+48, box.y+159), 580, 18)
            text(screen, stats, (box.x+48, box.y+258), 16, MINT)
            mouse = pygame.mouse.get_pos()
            button(screen, first, primary_label, hover=first.collidepoint(mouse))
            button(screen, second, 'Back to title', False, second.collidepoint(mouse))
            text(screen, 'ENTER  Continue     M Title     Q  Exit', (box.x+170, box.bottom+22), 13, (241,234,206))
        pygame.display.flip()
        clock.tick(60)
        if tracker is not None and tracker.show_preview():
            return 'quit'
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return 'quit'
                if event.key == pygame.K_F11:
                    fullscreen()
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r) or (pause and event.key in (pygame.K_p, pygame.K_ESCAPE)):
                    return primary_action
                elif event.key in (pygame.K_m, pygame.K_ESCAPE):
                    return 'menu'
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if first.collidepoint(event.pos):
                    return primary_action
                if second.collidepoint(event.pos):
                    return 'menu'
