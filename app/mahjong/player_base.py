from .shanten import calc_shanten


class PlayerBase:
    def __init__(self, player_id=None):
        self.id = player_id
        self.actions = {}

    # 汎用関数
    def prange(self):
        return [[i % 4, self.game.players[i % 4]] for i in range(self.position, self.position + 4)]

    def calc_shanten(self, add=[], remove=[]):
        tehai = [0] * 34
        for p in self.tehai:
            tehai[p // 4] += 1
        for p in add:
            tehai[p // 4] += 1
        for p in remove:
            tehai[p // 4] -= 1

        return calc_shanten(tehai, len(self.huro))
