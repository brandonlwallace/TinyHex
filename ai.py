# Small AI for the opponent: each unit moves and then attacks if possible.

import random
from entities import Unit
from astar import astar


class SimpleAI:
    def __init__(self, units, map_coords, terrain_map=None, record_attack=None):
        self.units = units
        self.map_coords = map_coords
        self.terrain_map = terrain_map or {}
        self.record_attack = record_attack

    def take_actions(self):
        # Each AI-owned unit gets to move (one tile, using A*) and attempt one attack if possible.
        ai_units = [u for u in self.units if u.owner == 1 and u.alive]
        player_units = [u for u in self.units if u.owner == 0 and u.alive]
        for u in ai_units:
            if not player_units:
                break
            target = min(player_units, key=lambda p: u.distance_to(p))
            if isinstance(u, Unit):
                # try melee if adjacent
                if u.distance_to(target) <= 1 and not u.has_attacked:
                    u.animate_attack(screen_stub(), target, stub_font())
                    hit, dmg = u.try_attack(target)
                    if self.record_attack:
                        self.record_attack(1, hit, dmg)
                    u.has_attacked = True
                else:
                    # Use A* to find a path to the target, avoiding rocks and occupied tiles
                    occupied = {(other.q, other.r) for other in self.units if other.alive and other != u}
                    path = astar((u.q, u.r), (target.q, target.r), self.map_coords, self.terrain_map, block_terrain=['rock'])
                    if path and len(path) > 1:
                        next_step = path[1]
                        if next_step not in occupied:
                            u.q, u.r = next_step
            u.has_moved = True
            u.has_attacked = True

# Stubs used above to allow animation calls without importing pygame into AI module
# These are replaced by real references in main.py after creating the AI
def screen_stub():
    return None

def stub_font():
    return None