"""Supersampled woodland mechanisms and animated portal tiles."""
import math
import pygame


def create_puzzle_tiles(size, textures):
    resolution = 192
    tiles = {}
    gold, silver = (221, 176, 89), (143, 192, 202)
    stone, edge, light = (79, 96, 79), (43, 62, 52), (157, 170, 137)

    def blank():
        return pygame.Surface((resolution, resolution), pygame.SRCALPHA)

    def finish(key, surface):
        tiles[key] = pygame.transform.smoothscale(surface, (size, size))

    def disc(s, center, radius, tint):
        pygame.draw.circle(s, (21, 37, 29, 85), (center[0]+2, center[1]+8), radius+3)
        pygame.draw.circle(s, edge, center, radius)
        pygame.draw.circle(s, tint, center, radius-5)
        pygame.draw.circle(s, light, center, radius-5, 2)

    def emblem(s, center, moon=False, tint=gold, radius=13):
        x, y = center
        pygame.draw.circle(s, tint, center, radius)
        if moon:
            pygame.draw.circle(s, stone, (x+radius//2, y-radius//3), radius-1)
        else:
            for i in range(8):
                a = i*math.tau/8
                pygame.draw.line(s, tint, (x+math.cos(a)*(radius+5), y+math.sin(a)*(radius+5)),
                                 (x+math.cos(a)*(radius+10), y+math.sin(a)*(radius+10)), 3)

    for on in (False, True):
        s = blank()
        disc(s, (96, 103), 68, stone)
        pygame.draw.circle(s, gold, (96, 103), 53, 3)
        for angle in (45, 135, 225, 315):
            a = math.radians(angle)
            p = (round(96+58*math.cos(a)), round(103+58*math.sin(a)))
            pygame.draw.circle(s, (187, 180, 135), p, 5)
            pygame.draw.line(s, edge, (p[0]-2, p[1]), (p[0]+2, p[1]), 2)
        pygame.draw.rect(s, edge, (77, 72, 38, 65), border_radius=17)
        pygame.draw.rect(s, (118, 133, 109), (83, 77, 26, 53), border_radius=12)
        end = (112, 72) if on else (80, 123)
        pygame.draw.line(s, (29, 43, 34), (96, 105), end, 15)
        pygame.draw.line(s, (206, 195, 145), (94, 101), (end[0]-2, end[1]-3), 7)
        pygame.draw.circle(s, silver if on else gold, end, 15)
        pygame.draw.circle(s, (246, 228, 171), (end[0]-4, end[1]-5), 4)
        emblem(s, (50, 101), radius=7)
        emblem(s, (143, 101), moon=True, tint=silver, radius=9)
        finish('S_on' if on else 'S', s)

    for key, tint in (('G', gold), ('H', silver)):
        for opened in (False, True):
            s = blank()
            pygame.draw.ellipse(s, (26, 42, 30, 85), (15, 144, 164, 25))
            for x in (23, 147):
                pygame.draw.rect(s, edge, (x, 34, 25, 124), border_radius=8)
                pygame.draw.rect(s, stone, (x+4, 38, 17, 114), border_radius=5)
                pygame.draw.rect(s, light, (x+3, 28, 20, 12), border_radius=3)
                pygame.draw.circle(s, tint, (x+12, 53), 6)
            if not opened:
                for x in (50, 77, 104, 131):
                    pygame.draw.rect(s, (65, 70, 49), (x, 52, 15, 91), border_radius=4)
                    pygame.draw.line(s, (142, 130, 83), (x+3, 56), (x+3, 138), 3)
                for y in (66, 126):
                    pygame.draw.rect(s, (72, 88, 72), (40, y, 112, 12), border_radius=3)
                    pygame.draw.line(s, tint, (44, y+2), (147, y+2), 2)
                disc(s, (96, 99), 26, stone)
                emblem(s, (96, 99), moon=key == 'H', tint=tint, radius=10)
            else:
                # Retracted gate leaves leave a clear walking channel.
                for x in (46, 136):
                    pygame.draw.rect(s, (100, 110, 78), (x, 61, 10, 82), border_radius=3)
                pygame.draw.ellipse(s, (*tint, 95), (49, 148, 94, 10))
            finish(key+('_open' if opened else ''), s)

    label_font = pygame.font.SysFont('DejaVu Sans', 28, bold=True)
    for pair, tint, number in (('AB', (175, 144, 227), '1'), ('UV', (103, 209, 194), '2')):
        for frame in range(16):
            s = blank()
            phase = frame*math.tau/16
            pygame.draw.ellipse(s, (20, 38, 30, 65), (12, 132, 168, 35))
            for pad in range(16, 1, -3):
                pygame.draw.ellipse(s, (*tint, 5+pad), (27-pad, 36-pad//2, 138+2*pad, 110+pad), 8)
            pygame.draw.ellipse(s, edge, (22, 34, 148, 118))
            pygame.draw.ellipse(s, (109, 126, 111), (27, 37, 138, 108), 10)
            pygame.draw.ellipse(s, (31, 53, 64), (37, 46, 118, 90))
            for inset in range(3):
                points = []
                for step in range(64):
                    a = step*math.tau/63
                    wave = 1+.04*math.sin(a*3+phase)
                    points.append((96+math.cos(a)*(55-inset*9)*wave,
                                   91+math.sin(a)*(39-inset*6)*wave))
                pygame.draw.lines(s, (*tint, 220-inset*55), True, points, 5-inset)
            spiral = []
            for step in range(92):
                a = phase+step*.13
                radius = 3+step*.42
                spiral.append((96+math.cos(a)*radius,91+math.sin(a)*radius*.64))
            pygame.draw.lines(s, (*tint, 95), False, spiral, 8)
            pygame.draw.lines(s, (*tint, 195), False, spiral, 3)
            for i in range(8):
                a = i*math.tau/8
                cx, cy = 96+math.cos(a)*66, 92+math.sin(a)*50
                pygame.draw.polygon(s, tint, [(cx,cy-4),(cx+3,cy),(cx,cy+4),(cx-3,cy)])
            for i in range(3):
                a = phase+i*math.tau/3
                pygame.draw.circle(s, (235, 245, 231), (round(96+math.cos(a)*43), round(91+math.sin(a)*29)), 4)
            disc(s, (96, 150), 20, stone)
            label = label_font.render(number, True, (241, 231, 195))
            s.blit(label, label.get_rect(center=(96,150)))
            reduced = pygame.transform.smoothscale(s, (size, size))
            for key in pair:
                tiles[f'{key}_{frame}'] = reduced
                if frame == 0:
                    tiles[key] = reduced

    # Stone storm paths have material and inlays instead of warning boxes.
    s = blank()
    pygame.draw.rect(s, (55, 75, 61, 100), (0, 20, 192, 158), border_radius=14)
    pygame.draw.rect(s, (114, 130, 107), (0, 15, 192, 151), border_radius=14)
    pygame.draw.line(s, (161, 170, 136), (0, 18), (192, 18), 3)
    pygame.draw.line(s, (68, 89, 74), (0, 162), (192, 162), 4)
    for x in (13, 179):
        for y in (32, 149):
            pygame.draw.circle(s, (181, 174, 131), (x, y), 4)
    pygame.draw.lines(s, (83, 102, 86), False, [(110,55),(87,95),(107,95),(82,132)], 5)
    finish('T', s)
    plank = textures['W'].copy()
    plank.blit(textures['L'], (0,0))
    # Natural cracks replace the bright rectangular outline.
    pygame.draw.lines(plank, (59, 47, 31), False, [(size//2, size//3), (size//2-4, size//2),
                                                            (size//2+4,size//2+4),(size//2,2*size//3)], 2)
    tiles['X'] = plank
    return tiles
