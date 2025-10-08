# Small AI for the opponent: each unit moves and then attacks if possible.
import random
from entities import Unit

class SimpleAI:
    def __init__(self, units, map_coords, terrain_map=None):
        self.units = units
        self.map_coords = map_coords
        self.terrain_map = terrain_map or {}

    def take_actions(self):
        # Each AI-owned unit gets to move (one tile) and attempt one attack if possible.
        ai_units = [u for u in self.units if u.owner == 1 and u.alive]
        player_units = [u for u in self.units if u.owner == 0 and u.alive]
        for u in ai_units:
            if not player_units:
                break
            # simple move: step closer along axis to nearest player unit
            target = min(player_units, key=lambda p: u.distance_to(p))
            if isinstance(u, Unit):
                # try melee if adjacent
                if u.distance_to(target) <= 1 and not u.has_attacked:
                    u.animate_attack(screen_stub(), target, stub_font())
                    u.try_attack(target)
                    u.has_attacked = True
                else:
                    # move into an unoccupied neighboring tile that reduces distance
                    moves = u.possible_moves(self.map_coords, self.terrain_map)
                    random.shuffle(moves)
                    best = (u.q, u.r)
                    bestd = u.distance_to(target)
                    for (mq, mr) in moves:
                        if any((other.q == mq and other.r == mr and other.alive) for other in self.units):
                            continue
                        # hypothetical distance
                        dq = abs(mq - target.q)
                        dr = abs(mr - target.r)
                        ds = abs((-mq-mr) - (-target.q-target.r))
                        nd = max(dq, dr, ds)
                        if nd < bestd:
                            bestd = nd
                            best = (mq, mr)
                    u.q, u.r = best
            # mark as acted -- AI handles both move and attack here
            u.has_moved = True
            u.has_attacked = True

# Stubs used above to allow animation calls without importing pygame into AI module
# These are replaced by real references in main.py after creating the AI
def screen_stub():
    return None

def stub_font():
    return None