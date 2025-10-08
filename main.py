# Main game file which runs the game

# Import packages and supporting files
import pygame
import sys
import random
from settings import *
from hexgrid import generate_hex_map, draw_map, axial_to_pixel, hex_corners
from entities import Unit, Longbow
from ai import SimpleAI, screen_stub, stub_font
import ui

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('TinyHex')
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 16)
font_title = pygame.font.SysFont('Times New Roman', 48, bold=True)
font_sub = pygame.font.SysFont('Arial', 20)

# Create basic terrain map: random small patches of forest and a few rocks (obstacles)
map_coords = generate_hex_map(MAP_RADIUS)

def generate_terrain(coords):
    tmap = {}
    # place a few rocks and forests deterministically for reproducibility
    candidates = coords.copy()
    random.shuffle(candidates)
    for i, c in enumerate(candidates[:4]):
        tmap[c] = TERRAIN_ROCK
    for j, c in enumerate(candidates[4:10]):
        if c not in tmap:
            tmap[c] = TERRAIN_FOREST
    return tmap

terrain_map = generate_terrain(map_coords)

# Unit spawning
def spawn_units():
    units = []
    spawnable = list(map_coords)
    random.shuffle(spawnable)
    # place simple units first
    for coord in spawnable:
        if len(units) >= MAX_UNITS:
            break
        q, r = coord
        # bias spawn by r coordinate
        if len([u for u in units if u.owner == 0]) < MAX_UNITS//2 and r < 1:
            units.append(Unit('P', q, r, owner=0))
        elif len([u for u in units if u.owner == 1]) < MAX_UNITS - MAX_UNITS//2 and r > -1:
            units.append(Unit('E', q, r, owner=1))
    # replace one unit on each side with a Longbow if available
    for side in [0, 1]:
        team = [u for u in units if u.owner == side]
        if team:
            victim = team[0]
            units.remove(victim)
            units.append(Longbow('L', victim.q, victim.r, owner=side))
    return units

units = spawn_units()

# Hook the AI stubs to real references
ai = SimpleAI(units, map_coords, terrain_map)
# monkey patch animation references expected by ai module
import ai as ai_module
ai_module.screen_stub = lambda: screen
ai_module.stub_font = lambda: font

# Game state
STATE_MENU = 'menu'
STATE_PLAYING = 'playing'
STATE_GAMEOVER = 'game_over'
state = STATE_MENU

current_turn = 0  # 0=player, 1=ai
selected_unit = None
valid_moves = []
message = ''

# UI rects
end_turn_rect = pygame.Rect(SCREEN_WIDTH - 170, 12, 150, 36)
reset_rect = pygame.Rect(SCREEN_WIDTH - 170, 58, 150, 36)
start_rect = pygame.Rect(SCREEN_WIDTH//2 - 90, SCREEN_HEIGHT//2 + 40, 180, 42)
quit_rect = pygame.Rect(SCREEN_WIDTH//2 - 90, SCREEN_HEIGHT//2 + 96, 180, 42)

# Helpers
def unit_at(q, r):
    for u in units:
        if u.alive and u.q == q and u.r == r:
            return u
    return None

def pixel_to_axial(mx, my):
    best = None
    bestd = 1e9
    for (q, r) in map_coords:
        x, y = axial_to_pixel(q, r)
        d = (x-mx)**2 + (y-my)**2
        if d < bestd:
            bestd = d
            best = (q, r)
    return best

# Track which units have acted this phase
def reset_action_flags(owner):
    for u in units:
        if u.owner == owner and u.alive:
            u.has_moved = False
            u.has_attacked = False

# End the current phase and switch sides
def end_turn():
    global current_turn, message, selected_unit, valid_moves
    selected_unit = None
    valid_moves = []
    current_turn = 1 - current_turn
    reset_action_flags(current_turn)
    message = f"{'Player' if current_turn==0 else 'AI'} phase."

# Reset the whole game without closing window
def reset_game():
    global units, ai, terrain_map, current_turn, state, message
    terrain_map = generate_terrain(map_coords)
    units = spawn_units()
    ai = SimpleAI(units, map_coords, terrain_map)
    # re-patch stubs
    ai_module.screen_stub = lambda: screen
    ai_module.stub_font = lambda: font
    current_turn = 0
    reset_action_flags(0)
    reset_action_flags(1)
    state = STATE_MENU
    message = 'Welcome back.'

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if state == STATE_MENU:
                if start_rect.collidepoint(mx, my):
                    state = STATE_PLAYING
                    message = 'Battle begins.'
                    # ensure fresh action flags
                    reset_action_flags(0)
                    reset_action_flags(1)
                elif quit_rect.collidepoint(mx, my):
                    running = False
            elif state == STATE_PLAYING:
                # UI buttons
                if end_turn_rect.collidepoint(mx, my):
                    end_turn()
                    continue
                if reset_rect.collidepoint(mx, my):
                    reset_game()
                    continue
                # Player actions only
                if current_turn == 0:
                    coord = pixel_to_axial(mx, my)
                    if not coord:
                        continue
                    q, r = coord
                    clicked = unit_at(q, r)
                    # NEW: Deselect if clicking same unit again 
                    if selected_unit and clicked == selected_unit:
                        selected_unit = None
                        valid_moves = []
                        message = 'Deselected unit.'
                        continue
                    if selected_unit is None:
                        # pick an unacted player's unit
                        if clicked and clicked.owner == 0 and (not clicked.has_moved or not clicked.has_attacked):
                            if clicked.owner == 0 and clicked.alive and (not clicked.has_moved or not clicked.has_attacked):
                                selected_unit = clicked
                                valid_moves = selected_unit.possible_moves(map_coords, terrain_map)
                                message = f'Selected unit at {selected_unit.q},{selected_unit.r}'
                        else:
                            message = 'Click an active (unexhausted) blue unit.'
                    else:
                        # If target is enemy and in attack range
                        if clicked and clicked.owner == 1 and not selected_unit.has_attacked:
                            # melee or ranged
                            if isinstance(selected_unit, Longbow):
                                if selected_unit.can_attack(clicked, units, terrain_map):
                                    selected_unit.animate_attack(screen, clicked, font)
                                    hit, dmg = selected_unit.try_attack(clicked)
                                    selected_unit.has_attacked = True
                                    message = f'Longbow attack -> hit={hit} dmg={dmg}'
                                    selected_unit = None
                                    valid_moves = []
                                else:
                                    message = 'Target out of range or no line of sight.'
                            else:
                                if selected_unit.distance_to(clicked) <= 1:
                                    selected_unit.animate_attack(screen, clicked, font)
                                    hit, dmg = selected_unit.try_attack(clicked)
                                    selected_unit.has_attacked = True
                                    message = f'Attack -> hit={hit} dmg={dmg}'
                                    selected_unit = None
                                    valid_moves = []
                                else:
                                    message = 'Enemy not adjacent.'
                        # Move
                        elif (q, r) in valid_moves and not selected_unit.has_moved:
                            # don't move into rock or occupied
                            if terrain_map.get((q, r)) == TERRAIN_ROCK:
                                message = 'Rock blocks movement.'
                            elif unit_at(q, r):
                                message = 'Tile occupied.'
                            else:
                                selected_unit.q, selected_unit.r = q, r
                                selected_unit.has_moved = True
                                message = f'Moved to {q},{r}'
                                selected_unit = None
                                valid_moves = []
                        else:
                            message = 'Invalid action or unit exhausted.'
            elif state == STATE_GAMEOVER:
                if reset_rect.collidepoint(mx, my):
                    reset_game()
                if quit_rect.collidepoint(mx, my):
                    running = False


    # AI phase automatic when it's AI's turn and state is playing
    if state == STATE_PLAYING and current_turn == 1:
        # AI will attempt to move + attack for each unit once
        ai.take_actions()
        end_turn()

    # Remove dead units
    units = [u for u in units if u.alive]

    # Victory check
    player_alive = any(u.owner == 0 and u.alive for u in units)
    ai_alive = any(u.owner == 1 and u.alive for u in units)
    if state == STATE_PLAYING and (not player_alive or not ai_alive):
        state = STATE_GAMEOVER
        winner = 'Player' if player_alive else 'AI'
        message = f'Game Over — {winner} wins.'

    # --- Render ---
    screen.fill(TAN)
    if state == STATE_MENU:
        # themed title screen with the map lightly visible in the background
        bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        draw_map(bg_surface, map_coords, terrain_map)
        bg_surface.set_alpha(140)
        screen.blit(bg_surface, (0, 0))
        ui.draw_title(screen, 'TinyHex', 'a tiny tactical hex wargame', font_title, font_sub, y_offset=60)
        ui.draw_button(screen, start_rect, 'Start Game', font_sub, bg=GREEN, fg=BLACK)
        ui.draw_button(screen, quit_rect, 'Quit', font_sub, bg=RED, fg=WHITE)
        footer = font_sub.render('by Brandon Wallace; prototype v.1.1', True, BLACK)
        screen.blit(footer, (12, SCREEN_HEIGHT - 36))
    elif state == STATE_PLAYING or state == STATE_GAMEOVER:
        # map and terrain
        draw_map(screen, map_coords, terrain_map)
        # highlights for valid moves
        if valid_moves:
            draw_map(screen, valid_moves, {}, highlight_set=set(valid_moves))
        # draw units
        for u in units:
            u.draw(screen, font)
        # UI buttons
        if state == STATE_PLAYING:
            ui.draw_button(screen, end_turn_rect, 'End Turn', font, bg=GRAY)
        ui.draw_button(screen, reset_rect, 'Reset', font, bg=GRAY)
        # turn & message
        turn_text = font.render(f'Turn: {"Player" if current_turn==0 else "AI"}', True, BLACK)
        screen.blit(turn_text, (8, 8))
        msg_text = font.render(message, True, BLACK)
        screen.blit(msg_text, (8, 28))
        # game over overlay
        if state == STATE_GAMEOVER:
            over = font_title.render('GAME OVER', True, BLACK)
            screen.blit(over, (SCREEN_WIDTH//2 - over.get_width()//2, SCREEN_HEIGHT//2 - 40))
            ui.draw_button(screen, reset_rect, 'Play Again', font, bg=GREEN)
            ui.draw_button(screen, quit_rect, 'Quit', font, bg=RED)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
