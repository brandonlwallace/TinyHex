# stats.py
# Game statistics and CSV export
import csv
import datetime

class GameStats:
    def __init__(self):
        self.turns = 0
        self.player_attacks = 0
        self.player_hits = 0
        self.player_damage = 0
        self.player_units_lost = 0
        self.ai_attacks = 0
        self.ai_hits = 0
        self.ai_damage = 0
        self.ai_units_lost = 0
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.winner = None
        # Per-unit stats: unit_id -> dict
        self.unit_stats = {}

    def register_unit(self, unit):
        # Call this when a unit is created
        self.unit_stats[unit.unit_id] = {
            'unit_id': unit.unit_id,
            'name': unit.name,
            'type': 'Archer' if hasattr(unit, 'range') else 'Ground',
            'owner': 'Player' if unit.owner == 0 else 'AI',
            'spawn_q': unit.q,
            'spawn_r': unit.r,
            'max_hp': unit.max_hp,
            'attacks': 0,
            'hits': 0,
            'damage_dealt': 0,
            'damage_taken': 0,
            'turn_spawned': self.turns,
            'turn_killed': None,
            'final_q': unit.q,
            'final_r': unit.r,
            'alive': True
        }

    def record_attack(self, owner, hit, dmg):
        if owner == 0:
            self.player_attacks += 1
            if hit:
                self.player_hits += 1
                self.player_damage += dmg
        else:
            self.ai_attacks += 1
            if hit:
                self.ai_hits += 1
                self.ai_damage += dmg

    def record_unit_lost(self, owner):
        if owner == 0:
            self.player_units_lost += 1
        else:
            self.ai_units_lost += 1

    def set_winner(self, winner):
        self.winner = winner
        self.end_time = datetime.datetime.now()

    def summary(self):
        return {
            'turns': self.turns,
            'player_attacks': self.player_attacks,
            'player_hits': self.player_hits,
            'player_damage': self.player_damage,
            'player_units_lost': self.player_units_lost,
            'ai_attacks': self.ai_attacks,
            'ai_hits': self.ai_hits,
            'ai_damage': self.ai_damage,
            'ai_units_lost': self.ai_units_lost,
            'winner': self.winner,
            'duration_seconds': (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        }

    def export_csv(self, filename):
        data = self.summary()
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Write summary first
            writer.writerow(['stat', 'value'])
            for k, v in data.items():
                writer.writerow([k, v])
            writer.writerow([])
            # Write per-unit stats table
            if self.unit_stats:
                unit_keys = [
                    'unit_id', 'name', 'type', 'owner', 'spawn_q', 'spawn_r', 'max_hp',
                    'attacks', 'hits', 'damage_dealt', 'damage_taken',
                    'turn_spawned', 'turn_killed', 'final_q', 'final_r', 'alive'
                ]
                writer.writerow(['Per-Unit Stats:'])
                writer.writerow(unit_keys)
                for u in self.unit_stats.values():
                    writer.writerow([u.get(k, '') for k in unit_keys])
