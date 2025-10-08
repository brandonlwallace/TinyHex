# Definitions for characters/units including simple combat logic, animation, and ranged unit.
import random
import pygame
from hexgrid import axial_to_pixel
from settings import RED, BLUE, BLACK, FOREST, TERRAIN_FOREST, TERRAIN_ROCK

class Unit:
    # A minimal unit with health, attack, movement, owner (0=player,1=AI)
    def __init__(self, name, q, r, owner=0):
        self.name = name
        self.q = q
        self.r = r
        self.owner = owner
        self.max_hp = 10
        self.hp = self.max_hp
        self.attack = 4
        self.move_range = 2
        self.alive = True
        # action flags used for turn-by-turn activation
        self.has_moved = False
        self.has_attacked = False

    def pixel_pos(self):
        return axial_to_pixel(self.q, self.r)

    def distance_to(self, other):
        # axial distance via cube coordinates
        dq = abs(self.q - other.q)
        dr = abs(self.r - other.r)
        ds = abs((-self.q-self.r) - (-other.q-other.r))
        return max(dq, dr, ds)

    def possible_moves(self, map_coords, terrain_map=None):
        # Returns axial coords within move_range and on-map (no pathfinding)
        results = []
        for (cq, cr) in map_coords:
            dq = abs(self.q - cq)
            dr = abs(self.r - cr)
            ds = abs((-self.q-self.r) - (-cq-cr))
            dist = max(dq, dr, ds)
            effective_range = self.move_range
            # If terrain is forest at destination, cost is effectively higher (reduce allowed range by 1)
            if terrain_map and terrain_map.get((cq, cr)) == TERRAIN_FOREST:
                effective_range = max(1, effective_range - 1)
            if dist <= effective_range and (self.q, self.r) != (cq, cr):
                results.append((cq, cr))
        return results

    def try_attack(self, target):
        # Probabilistic adjudication: hit chance depends on relative HP and randomness
        if not target or not target.alive:
            return False, 0
        base_hit = 0.6
        hp_factor = max(-0.2, min(0.2, (self.hp - target.hp) / self.max_hp))
        hit_chance = base_hit + hp_factor
        roll = random.random()
        if roll <= hit_chance:
            # damage is probabilistic around attack stat
            dmg = max(1, int(random.gauss(self.attack, 1)))
            target.hp -= dmg
            if target.hp <= 0:
                target.alive = False
            return True, dmg
        else:
            return False, 0

    def animate_attack(self, surface, target, font, shake_intensity=6, flashes=2):
        """Simple flash and shake animation when this unit attacks a target.
        This blocks briefly to show feedback (simple and effective for prototypes).
        """
        import time
        orig_surf = surface.copy()
        sx, sy = self.pixel_pos()
        tx, ty = target.pixel_pos()

        for i in range(flashes):
            # flash attacker and target by drawing white circles behind them
            surface.blit(orig_surf, (0,0))
            pygame.draw.circle(surface, (255,255,255), (sx, sy), 18)
            pygame.draw.circle(surface, (255,255,255), (tx, ty), 18)
            pygame.display.flip()
            time.sleep(0.06)
            # small shake
            for _ in range(3):
                surface.blit(orig_surf, (0,0))
                ox = random.randint(-shake_intensity, shake_intensity)
                oy = random.randint(-shake_intensity, shake_intensity)
                # draw both units offset
                col_s = BLUE if self.owner == 0 else RED
                col_t = BLUE if target.owner == 0 else RED
                pygame.draw.circle(surface, col_s, (sx + ox, sy + oy), 14)
                pygame.draw.circle(surface, col_t, (tx + -ox, ty + -oy), 14)
                # damage text
                pygame.display.flip()
                time.sleep(0.03)
        # restore
        surface.blit(orig_surf, (0,0))
        pygame.display.flip()

    def draw(self, surface, font):
        x, y = self.pixel_pos()
        col = BLUE if self.owner == 0 else RED
        # draw a filled circle inside the hex for unit
        pygame.draw.circle(surface, col, (x, y), 14)
        txt = font.render(str(self.hp), True, BLACK)
        surface.blit(txt, (x - txt.get_width()//2, y - txt.get_height()//2))

# Longbow special unit
class Longbow(Unit):
    """Ranged unit. Can attack at a distance if line of sight is clear.
    It is represented as a triangle icon.
    """
    def __init__(self, name, q, r, owner=0):
        super().__init__(name, q, r, owner)
        self.attack = 3
        self.range = 3

    def has_line_of_sight(self, target, units, terrain_map=None):
        # LOS only allowed along straight axial lines (q, r, or s-axis)
        dq = target.q - self.q
        dr = target.r - self.r
        ds = -dq-dr
        steps = max(abs(dq), abs(dr), abs(ds))
        if steps == 0 or steps > self.range:
            return False
        # direction increments (must be integer steps along axial axes)
        step_q = 0 if dq == 0 else dq // abs(dq)
        step_r = 0 if dr == 0 else dr // abs(dr)
        # march along the line and check for blocking units or rock terrain
        for i in range(1, steps):
            cq = self.q + step_q * i
            cr = self.r + step_r * i
            # terrain blocking
            if terrain_map and terrain_map.get((cq, cr)) == TERRAIN_ROCK:
                return False
            # unit blocking
            if any(u.alive and u.q == cq and u.r == cr for u in units):
                return False
        return True

    def can_attack(self, target, units, terrain_map=None):
        return (self.alive and target.alive and self.distance_to(target) <= self.range
                and self.has_line_of_sight(target, units, terrain_map))

    def draw(self, surface, font):
        x, y = self.pixel_pos()
        # triangle pointing up for player, down for AI
        if self.owner == 0:
            pts = [(x, y-12), (x-10, y+10), (x+10, y+10)]
            col = (20, 140, 140)
        else:
            pts = [(x, y+12), (x-10, y-10), (x+10, y-10)]
            col = (140, 20, 140)
        pygame.draw.polygon(surface, col, pts)
        txt = font.render(str(self.hp), True, BLACK)
        surface.blit(txt, (x - txt.get_width()//2, y - txt.get_height()//2))
