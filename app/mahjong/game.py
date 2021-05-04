from .game_action import GameAction
from .game_base import GameBase
from .game_routine import GameRoutine

# TODO リーチ後のカンできるかどうか
# TODO 喰い替え禁止


class Game(GameBase, GameAction, GameRoutine):
    pass
