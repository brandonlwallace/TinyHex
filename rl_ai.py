# Reinforcement Learning based AI for the opponent
# Uses weighted heuristics that improve through self-play

import random
import json
import os
from entities import Unit
from astar import astar


class RLAI:
    """Intelligent AI opponent using learned weights and strategic decision-making."""
    
    # Default weights for evaluating moves/attacks
    DEFAULT_WEIGHTS = {
        'target_hp_weight': 0.8,           # Prefer lower HP targets
        'target_distance_weight': 0.3,     # Prefer closer targets
        'target_threat_weight': 1.2,       # Prefer targets that threaten us
        'terrain_defense_weight': 0.5,     # Prefer moving to forest
        'safety_weight': 1.0,              # Avoid positions with many enemies
        'focus_fire_weight': 0.6,          # Prefer targets allies are attacking
        'retreat_threshold': 0.35,         # HP ratio below which to retreat
        'formation_weight': 0.4,           # Prefer staying near allies
    }
    
    def __init__(self, units, map_coords, terrain_map=None, record_attack=None, weights_file='rl_weights.json'):
        self.units = units
        self.map_coords = map_coords
        self.terrain_map = terrain_map or {}
        self.record_attack = record_attack
        self.weights_file = weights_file
        self.weights = self.load_weights()
        self.game_history = []  # Track decisions for learning
        
    def load_weights(self):
        """Load learned weights from file, or use defaults."""
        if os.path.exists(self.weights_file):
            try:
                with open(self.weights_file, 'r') as f:
                    return json.load(f)
            except:
                return self.DEFAULT_WEIGHTS.copy()
        return self.DEFAULT_WEIGHTS.copy()
    
    def save_weights(self):
        """Save current weights to file for next game."""
        try:
            with open(self.weights_file, 'w') as f:
                json.dump(self.weights, f, indent=2)
        except:
            pass  # Silently fail if can't write
    
    def update_weights_from_game(self, ai_won):
        """Adjust weights based on game outcome using simple RL."""
        if not self.game_history:
            return
        
        # Winning: reinforce decisions that led to victory
        # Losing: reduce weight of poor decisions
        adjustment = 0.02 if ai_won else -0.01
        
        # Analyze which strategies were used most
        if ai_won:
            # Boost strategies used when winning
            if any(h['action'] == 'attack' for h in self.game_history):
                self.weights['target_threat_weight'] *= (1 + adjustment)
                self.weights['focus_fire_weight'] *= (1 + adjustment)
            if any(h.get('used_terrain') for h in self.game_history):
                self.weights['terrain_defense_weight'] *= (1 + adjustment)
            if any(h.get('survived_weak') for h in self.game_history):
                self.weights['safety_weight'] *= (1 + adjustment)
        else:
            # Penalize strategies used when losing
            if any(h['action'] == 'move_into_danger' for h in self.game_history):
                self.weights['safety_weight'] *= (1 - adjustment)
            # Don't get too aggressive if losing
            self.weights['target_threat_weight'] *= (1 - abs(adjustment))
        
        # Keep weights in reasonable bounds
        for key in self.weights:
            self.weights[key] = max(0.1, min(2.0, self.weights[key]))
        
        self.save_weights()
        self.game_history = []
    
    def evaluate_target(self, ai_unit, target, player_units):
        """Score how attractive a target is (higher = better)."""
        if not target.alive:
            return -1000
        
        # Base score from HP (lower is better)
        hp_score = (target.max_hp - target.hp) / target.max_hp
        
        # Distance score (closer is better)
        distance = ai_unit.distance_to(target)
        distance_score = 1.0 / (distance + 1)
        
        # Threat score: how much damage does target do?
        threat_score = target.attack / 10.0  # Normalized by typical attack value
        
        # Ranged threat (Longbows are more dangerous)
        if hasattr(target, 'range'):
            threat_score *= 1.5
        
        # Coordination score: are allies already attacking this target?
        allies_attacking = sum(1 for u in [u2 for u2 in self.units if u2.owner == 1 and u2.alive and u2 != ai_unit]
                              if hasattr(u, 'last_attack_target') and u.last_attack_target == target)
        focus_score = allies_attacking * 0.2
        
        # Composite score using learned weights
        score = (
            self.weights['target_hp_weight'] * hp_score +
            self.weights['target_distance_weight'] * distance_score +
            self.weights['target_threat_weight'] * threat_score +
            self.weights['focus_fire_weight'] * focus_score
        )
        
        return score
    
    def evaluate_position(self, ai_unit, position, player_units):
        """Score how safe a position is (higher = safer)."""
        safety = 1.0
        
        # Count enemies adjacent to this position
        q, r = position
        adjacent_enemies = 0
        for dq, dr in [(1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1)]:
            check = (q + dq, r + dr)
            if any(u.alive and u.owner == 0 and u.q == check[0] and u.r == check[1] for u in self.units):
                adjacent_enemies += 1
        
        # Penalize being surrounded
        safety -= adjacent_enemies * self.weights['safety_weight'] * 0.2
        
        # Bonus for terrain defense
        if self.terrain_map.get(position) == 'forest':
            safety += self.weights['terrain_defense_weight'] * 0.3
        
        # Bonus for being near allies
        ally_distance = min([ai_unit.distance_to(u) for u in self.units 
                            if u.owner == 1 and u.alive and u != ai_unit] or [5])
        if ally_distance <= 2:
            safety += self.weights['formation_weight'] * (2 - ally_distance) * 0.1
        
        return max(0.1, safety)
    
    def should_retreat(self, ai_unit):
        """Decide if unit should flee (when heavily outnumbered or low HP)."""
        hp_ratio = ai_unit.hp / ai_unit.max_hp
        if hp_ratio < self.weights['retreat_threshold']:
            return True
        
        # Retreat if surrounded
        q, r = ai_unit.q, ai_unit.r
        adjacent_enemies = sum(1 for dq, dr in [(1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1)]
                              if any(u.alive and u.owner == 0 and u.q == q+dq and u.r == r+dr for u in self.units))
        if adjacent_enemies >= 3:
            return True
        
        return False
    
    def find_retreat_position(self, ai_unit, player_units):
        """Find safest position to move to."""
        possible = ai_unit.possible_moves(self.map_coords, self.terrain_map)
        occupied = {(u.q, u.r) for u in self.units if u.alive and u != ai_unit}
        valid = [p for p in possible if p not in occupied and 
                self.terrain_map.get(p) != 'rock']
        
        if not valid:
            return None
        
        # Choose position with best safety score
        return max(valid, key=lambda p: self.evaluate_position(ai_unit, p, player_units))
    
    def take_actions(self):
        """Main AI turn: move and attack all units."""
        ai_units = [u for u in self.units if u.owner == 1 and u.alive]
        player_units = [u for u in self.units if u.owner == 0 and u.alive]
        
        if not player_units:
            return
        
        for u in ai_units:
            if not player_units:
                break
            
            # Check if should retreat
            if self.should_retreat(u):
                retreat_pos = self.find_retreat_position(u, player_units)
                if retreat_pos and not u.has_moved:
                    u.q, u.r = retreat_pos
                    u.has_moved = True
                    self.game_history.append({'action': 'retreat', 'unit': u.name})
                continue
            
            # Pick best target using learned weights
            targets_with_scores = [(t, self.evaluate_target(u, t, player_units)) 
                                  for t in player_units]
            targets_with_scores.sort(key=lambda x: x[1], reverse=True)
            target = targets_with_scores[0][0]
            
            # Try ranged attack if unit has it
            if hasattr(u, 'range') and not u.has_attacked:
                if u.can_attack(target, self.units, self.terrain_map):
                    self._execute_attack(u, target)
                    u.has_moved = True
                    continue
            
            # Try melee attack if adjacent
            if u.distance_to(target) <= 1 and not u.has_attacked:
                self._execute_attack(u, target)
                u.has_moved = True
                continue
            
            # Otherwise move toward target using A*
            if not u.has_moved:
                occupied = {(other.q, other.r) for other in self.units 
                           if other.alive and other != u}
                path = astar((u.q, u.r), (target.q, target.r), self.map_coords,
                            self.terrain_map, block_terrain=['rock'])
                
                if path and len(path) > 1:
                    next_step = path[1]
                    if next_step not in occupied:
                        u.q, u.r = next_step
                        u.has_moved = True
                        
                        # Track if moved to terrain
                        if self.terrain_map.get(next_step) == 'forest':
                            self.game_history.append({'action': 'move', 'used_terrain': True})
            
            u.has_attacked = False
    
    def _execute_attack(self, attacker, target):
        """Execute attack and record it."""
        # Animate attack (animation stubs replaced by main.py)
        if hasattr(attacker, 'animate_attack'):
            attacker.animate_attack(screen_stub(), target, stub_font())
        
        hit, dmg = attacker.try_attack(target, terrain_map=self.terrain_map, stats=None, turn=None)
        
        if self.record_attack:
            self.record_attack(1, hit, dmg)
        
        attacker.last_attack_result = (hit, dmg, target)
        attacker.last_attack_target = target  # Track for focus fire
        attacker.has_attacked = True
        
        self.game_history.append({
            'action': 'attack',
            'hit': hit,
            'damage': dmg,
            'target_hp': target.hp
        })
        
        # Check if survived weak position
        if hit and target.hp > 0:
            self.game_history[-1]['survived_weak'] = target.hp < target.max_hp / 2


# Stubs for animation calls
def screen_stub():
    return None

def stub_font():
    return None
