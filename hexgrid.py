# Hex grid logic and drawing helpers. Uses axial coordinates (q, r).
import math
import pygame
from settings import HEX_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, FOREST, ROCK, TAN, TERRAIN_FOREST, TERRAIN_ROCK

# Convert axial (q, r) to pixel coordinates (x, y) for pointy-top hexes
def axial_to_pixel(q, r, size=HEX_SIZE, origin=None):
    if origin is None:
        origin = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    x = size * (math.sqrt(3) * q + math.sqrt(3)/2 * r) + origin[0]
    y = size * (3/2 * r) + origin[1]
    return (int(x), int(y))

# Get polygon points for a hex centered at pixel (x, y)
def hex_corners(x, y, size=HEX_SIZE):
    points = []
    for i in range(6):
        angle = math.pi/180 * (60 * i - 30)  # pointy-top
        px = x + size * math.cos(angle)
        py = y + size * math.sin(angle)
        points.append((px, py))
    return points

# Generate a small hex-shaped map using axial coordinates within a radius
def generate_hex_map(radius):
    coords = []
    for q in range(-radius, radius+1):
        r1 = max(-radius, -q-radius)
        r2 = min(radius, -q+radius)
        for r in range(r1, r2+1):
            coords.append((q, r))
    return coords

# Draw the whole map; accepts a terrain dict mapping coords -> terrain type
def draw_map(surface, coords, terrain_map=None, highlight_set=None, origin=None):
    for (q, r) in coords:
        x, y = axial_to_pixel(q, r, origin=origin)
        pts = hex_corners(x, y)
        terrain = terrain_map.get((q, r), None) if terrain_map else None
        if terrain == TERRAIN_FOREST:
            color = FOREST
        elif terrain == TERRAIN_ROCK:
            color = ROCK
        else:
            color = TAN
        pygame.draw.polygon(surface, color, pts)
        pygame.draw.polygon(surface, (100, 80, 60), pts, 2)
        if highlight_set and (q, r) in highlight_set:
            pygame.draw.polygon(surface, (240, 240, 180), pts, 0)
