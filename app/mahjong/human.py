from .player import Player


class Human(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'human'
