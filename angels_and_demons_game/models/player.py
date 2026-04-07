class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0

        self.turns_taken = 0
        self.boxes_opened = 0
        self.effects_triggered = 0
        self.positive_swings = 0
        self.negative_swings = 0
        self.biggest_gain = 0
        self.biggest_loss = 0
        self.steal_points = 0
        self.shield_blocks = 0
        self.bonus_turns_earned = 0

        self.shields = 0
        self.skip_turns = 0
        self.bonus_turns = 0

    def add_score(self, amount):
        self.apply_score_delta(int(round(amount)))

    def subtract_score(self, amount):
        self.apply_score_delta(-int(round(amount)))

    def apply_score_delta(self, delta):
        delta = int(delta)
        self.score += delta
        if delta > 0:
            self.positive_swings += 1
            self.biggest_gain = max(self.biggest_gain, delta)
        elif delta < 0:
            self.negative_swings += 1
            self.biggest_loss = max(self.biggest_loss, abs(delta))
        return delta

    def set_score(self, new_score):
        new_score = int(round(new_score))
        delta = new_score - self.score
        self.apply_score_delta(delta)
        return delta

    def record_turn(self):
        self.turns_taken += 1

    def record_box_opened(self):
        self.boxes_opened += 1
        self.effects_triggered += 1

    def record_steal(self, amount):
        self.steal_points += max(0, int(amount))

    def grant_shield(self, amount=1):
        amount = max(0, int(amount))
        self.shields += amount
        return self.shields

    def consume_shield(self):
        if self.shields <= 0:
            return False
        self.shields -= 1
        self.shield_blocks += 1
        return True

    def grant_skip_turn(self, amount=1):
        amount = max(0, int(amount))
        self.skip_turns += amount
        return self.skip_turns

    def consume_skip_turn(self):
        if self.skip_turns <= 0:
            return False
        self.skip_turns -= 1
        return True

    def grant_bonus_turn(self, amount=1):
        amount = max(0, int(amount))
        self.bonus_turns += amount
        self.bonus_turns_earned += amount
        return self.bonus_turns

    def consume_bonus_turn(self):
        if self.bonus_turns <= 0:
            return False
        self.bonus_turns -= 1
        return True

