from .player_action import PlayerAction
from .player_message import PlayerMessage
from .player_judge import PlayerJudge


class Player(PlayerAction, PlayerJudge, PlayerMessage):
    def __init__(self, player_id=None):
        self.id = player_id
        self.actions = {}

    # 汎用関数
    def prange(self):
        return [[i % 4, self.game.players[i % 4]] for i in range(self.position, self.position + 4)]
