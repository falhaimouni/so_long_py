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

_window_size = SIZE
_fullscreen = False


def render_scale():
    surface = pygame.display.get_surface()
    if surface is None:
        return 1.0
    w, h = surface.get_size()
    return min(w / SIZE[0], h / SIZE[1])


def point(position):
    scale = render_scale()
    surface = pygame.display.get_surface()
    w, h = surface.get_size() if surface is not None else SIZE
    return (round((w-SIZE[0]*scale)/2 + position[0]*scale),
            round((h-SIZE[1]*scale)/2 + position[1]*scale))


def rect(bounds):
    bounds = pygame.Rect(bounds)
    return pygame.Rect(point(bounds.topleft),
                       (round(bounds.width*render_scale()), round(bounds.height*render_scale())))


def length(value):
    return max(1, round(value * render_scale()))


def mouse_position(position=None):
    x, y = pygame.mouse.get_pos() if position is None else position
    surface = pygame.display.get_surface()
    w, h = surface.get_size()
    scale = render_scale()
    return ((x-(w-SIZE[0]*scale)/2)/scale, (y-(h-SIZE[1]*scale)/2)/scale)


@lru_cache(maxsize=64)
def _font(pixel_size, serif):
    return pygame.font.SysFont('DejaVu Serif' if serif else 'DejaVu Sans', pixel_size)


def font(size, serif=False):
    return _font(length(size), serif)


def text(surface, copy, pos, size=18, color=CREAM, serif=False):
    image = font(size, serif).render(str(copy), True, color)
    surface.blit(image, point(pos))
    return image.get_rect(topleft=point(pos))


def wrapped(surface, copy, pos, width, size=17, color=MUTED):
    x, y = pos
    line = ''
    for word in copy.split():
        candidate = (line + ' ' + word).strip()
        if font(size).size(candidate)[0] > width * render_scale() and line:
            text(surface, line, (x, y), size, color)
            y += size + 9
            line = word
        else:
            line = candidate
    if line:
        text(surface, line, (x, y), size, color)
        y += size + 9
    return y


def panel(surface, bounds, fill=PANEL):
    pygame.draw.rect(surface, fill, rect(bounds), border_radius=length(18))
    pygame.draw.rect(surface, BORDER, rect(bounds), length(1), border_radius=length(18))


def button(surface, bounds, label, primary=True, hover=False):
    bounds = pygame.Rect(bounds)
    target = rect(bounds)
    fill = (92, 145, 76) if primary and hover else MINT if primary else (231, 240, 213) if hover else PANEL
    pygame.draw.rect(surface, fill, target, border_radius=length(10))
    if not primary:
        pygame.draw.rect(surface, BORDER, target, length(1), border_radius=length(10))
    image = font(18).render(label, True, (249, 241, 215) if primary else CREAM)
    surface.blit(image, image.get_rect(center=target.center))
    return bounds


def create_display():
    global _window_size
    _font.cache_clear()
    current = pygame.display.get_surface()
    if current is not None:
        return current
    desktop = pygame.display.get_desktop_sizes()[0]
    scale = min(1.0, desktop[0]*.9/SIZE[0], desktop[1]*.9/SIZE[1])
    _window_size = (round(SIZE[0]*scale), round(SIZE[1]*scale))
    screen = pygame.display.set_mode(_window_size, pygame.RESIZABLE)
    pygame.display.set_caption('Rabbit Adventure | The Woodland Trials')
    return screen


def fullscreen():
    global _fullscreen, _window_size
    screen = pygame.display.get_surface()
    if not _fullscreen:
        _window_size = screen.get_size()
        pygame.display.set_mode(pygame.display.get_desktop_sizes()[0], pygame.FULLSCREEN)
    else:
        pygame.display.set_mode(_window_size, pygame.RESIZABLE)
    _fullscreen = not _fullscreen



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
    _font.cache_clear()
    clock = pygame.time.Clock()
    instructions = False
    while True:
        screen = pygame.display.get_surface()
        screen.blit(title_art(screen.get_size()), (0, 0))
        w, h = SIZE
        sx, sy = 1, 1
        # Title remains usable in the original small window used by embedders.
        x, top = round(72*sx), round(120*sy)
        text(screen, 'A HAND-CONTROLLED WOODLAND ADVENTURE', (x, top), 14, MINT)
        text(screen, 'Rabbit', (x-4, top+42), 76 if w >= 1100 else 60, serif=True)
        text(screen, 'Adventure', (x-4, top+130), 76 if w >= 1100 else 60, serif=True)
        text(screen, 'T H E   W O O D L A N D   T R I A L S', (x, top+237), 16, GOLD)
        wrapped(screen, 'Collect the carrots. Find your way home.', (x, top+300), 420, 22, CREAM)
        mouse = mouse_position()
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
                    if help_start.collidepoint(mouse_position(event.pos)):
                        return True
                elif play_rect.collidepoint(mouse_position(event.pos)):
                    return True
                elif help_rect.collidepoint(mouse_position(event.pos)):
                    instructions = True


def draw_hud(screen, level, total, title, hint, coins, initial_coins, danger, gate):
    """Keep the board central, with only a slim header and a short hint."""
    screen.fill(INK)
    panel(screen, pygame.Rect(40, 22, 1216, 56))
    text(screen, f'{level+1:02d} / {total:02d}', (64, 40), 15, MUTED)
    text(screen, title, (170, 35), 23, serif=True)
    collected = initial_coins - coins
    text(screen, f'Carrots  {collected} / {initial_coins}', (1074, 39), 17, MINT)
    instruction = 'All carrots collected! Head to the burrow.' if coins == 0 else hint
    rendered = font(16).render(instruction, True, (249, 242, 217))
    screen.blit(rendered, rendered.get_rect(center=point((520, 824))))
    status = '  /  '.join(part for part in (gate, danger) if part)
    if status:
        rendered = font(13).render(status, True, (250, 215, 151))
        screen.blit(rendered, rendered.get_rect(center=point((520, 849))))
    rendered = font(12).render('WASD / arrows or point to move   ·   Palm / fist to stop   ·   P Pause   ·   R Retry   ·   F11 Fullscreen   ·   Q Exit', True, (222, 231, 204))
    screen.blit(rendered, rendered.get_rect(center=point((640, 879))))


def draw_camera(screen, tracker):
    """A small live camera card sits outside the playable board."""
    card = pygame.Rect(1024, 98, 232, 250)
    panel(screen, card)
    text(screen, 'HAND CONTROL', (1038, 111), 12, MUTED)
    viewport = rect((1032, 138, 216, 162))
    pygame.draw.rect(screen, (36, 55, 42), viewport, border_radius=length(8))
    preview, state = tracker.preview_surface(viewport.size)
    if preview is not None:
        screen.blit(preview, viewport)
        label = state.direction.upper() if state.direction else state.gesture
        tint = MINT if state.direction else MUTED
    else:
        starting = state.status == 'Starting camera'
        label = 'Starting camera...' if starting else 'Keyboard ready'
        tint = MUTED
        image = font(14).render('Starting camera...' if starting else 'Camera unavailable', True, (225, 232, 206))
        screen.blit(image, image.get_rect(center=viewport.center))
    pygame.draw.circle(screen, tint, point((1042, 322)), length(4))
    text(screen, label, (1054, 311), 13, tint)


def draw_happy_ending(screen, stats, elapsed):
    screen.blit(background_art('ending.png', screen.get_size()), (0,0))
    w, h = SIZE
    # Petals drift through the scene; the success screen stays alive until input.
    for i in range(32):
        x = (i*137+math.sin(elapsed*.6+i)*28) % w
        y = (i*83+elapsed*(18+i%5*4)) % h
        tint = ((232, 186, 90), (243, 217, 151), (172, 192, 113))[i%3]
        pygame.draw.ellipse(screen, tint, rect((round(x),round(y),7+i%3,4+i%2)))
    box = pygame.Rect(52, 90, 580, 718)
    target = rect(box)
    glass = pygame.Surface(target.size, pygame.SRCALPHA)
    pygame.draw.rect(glass, (33, 58, 41, 237), glass.get_rect(), border_radius=length(24))
    pygame.draw.rect(glass, (183, 172, 115, 160), glass.get_rect(), length(1), border_radius=length(24))
    screen.blit(glass, target)
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
        pygame.draw.circle(screen, (96, 116, 67), point((cx,cy)), length(27))
        pygame.draw.circle(screen, gold, point((cx,cy)), length(25), length(1))
        points = []
        for j in range(10):
            angle = j*math.pi/5-math.pi/2
            radius = 15 if j%2 == 0 else 7
            points.append(point((cx+math.cos(angle)*radius,cy+math.sin(angle)*radius)))
        pygame.draw.polygon(screen, gold, points)
    text(screen, 'ALL SIX TRIALS COMPLETE', (90, 582), 14, gold)
    text(screen, 'Final trail: '+stats, (90, 624), 13, (205,220,179))
    first = pygame.Rect(90, 690, 240, 56)
    second = pygame.Rect(346, 690, 240, 56)
    mouse = mouse_position()
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
    w, h = SIZE
    box = pygame.Rect((w-680)//2, (h-430)//2, 680, 430)
    first = pygame.Rect(box.x+48, box.bottom-93, 282, 56)
    second = pygame.Rect(box.x+348, box.bottom-93, 282, 56)
    started_at = pygame.time.get_ticks()
    while True:
        screen = pygame.display.get_surface()
        if frozen.get_size() != screen.get_size():
            frozen = pygame.transform.smoothscale(frozen, screen.get_size())
        if kind == 'complete':
            first, second = draw_happy_ending(screen, stats, (pygame.time.get_ticks()-started_at)/1000)
        else:
            screen.blit(frozen, (0, 0))
            panel(screen, box)
            text(screen, {'pause': 'TAKE A BREATHER', 'lost': 'THE FOREST HAS ANOTHER CHANCE', 'next': 'TRIAL COMPLETE', 'complete': 'ALL SIX TRIALS COMPLETE'}[kind], (box.x+48, box.y+37), 13, GOLD)
            text(screen, title, (box.x+48, box.y+84), 40, serif=True)
            wrapped(screen, copy, (box.x+48, box.y+159), 580, 18)
            text(screen, stats, (box.x+48, box.y+258), 16, MINT)
            mouse = mouse_position()
            button(screen, first, primary_label, hover=first.collidepoint(mouse))
            button(screen, second, 'Back to title', False, second.collidepoint(mouse))
            text(screen, 'ENTER  Continue     M Title     Q  Exit', (box.x+170, box.bottom+22), 13, (241,234,206))
        if tracker is not None and kind != 'complete':
            draw_camera(screen, tracker)
        pygame.display.flip()
        clock.tick(60)
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
                if first.collidepoint(mouse_position(event.pos)):
                    return primary_action
                if second.collidepoint(mouse_position(event.pos)):
                    return 'menu'
