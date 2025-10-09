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
            writer.writerow(['stat', 'value'])
            for k, v in data.items():
                writer.writerow([k, v])
