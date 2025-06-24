# player.py - auto-generated

class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0

    def add_score(self, amount):
        self.score += amount

    def subtract_score(self, amount):
        self.score -= amount

