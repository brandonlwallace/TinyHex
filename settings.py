# Global settings and constants for the game.
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 720
FPS = 60

# Hex parameters (pointy-top hexes)
HEX_SIZE = 36  # radius
MAP_RADIUS = 3  # small map

# Colors (R,G,B) - flat palette for a "themed" look
WHITE = (245, 240, 230)
BLACK = (10, 10, 10)
GRAY = (170, 170, 170)
DARK_GRAY = (120, 120, 120)
RED = (200, 50, 50)
BLUE = (50, 80, 200)
GREEN = (60, 160, 80)
TAN = (220, 200, 160)
BROWN = (140, 100, 60)
FOREST = (50, 110, 60)
ROCK = (100, 100, 110)

# Game limits
MAX_UNITS = 12

# Terrain types
TERRAIN_PLAIN = 'plain'
TERRAIN_FOREST = 'forest'  # reduces movement effectiveness
TERRAIN_ROCK = 'rock'      # blocks movement & line-of-sight