from .shanten import calc_shanten


class Player():
    def __init__(self, player_id=None):
        self.id = player_id

    def prange(self):
        return [i % 4 for i in range(self.position, self.position + 4)]

    def reset_action(self):
        self.last_action = []

    def start_game(self):
        pass

    def start_kyoku(self):
        self.tehai = []
        self.huro = []
        self.kawa = []

    def tsumo(self, pai):
        self.tehai.append(pai)
        self.tehai.sort()

    def my_tsumo(self, tsumo):
        self.last_action.append({
            'type': 'my_tsumo',
            'body': {
                'tsumo': tsumo,
                'rest': len(self.game.yama)
            }
        })

    def other_tsumo(self, tsumo):
        self.last_action.append({
            'type': 'other_tsumo',
            'body': {
                'tsumo': self.game.make_dummy(tsumo),
                'who': (self.game.teban - self.position) % 4,
                'rest': len(self.game.yama)
            }
        })

    def my_dahai(self, dahai):
        self.last_action.append({
            'type': 'my_dahai',
            'body': {
                'dahai': dahai
            }
        })

    def other_dahai(self, dahai):
        self.last_action.append({
            'type': 'other_dahai',
            'body': {
                'dahai': dahai,
                'dummy': self.game.make_dummy(dahai),
                'who': (self.game.teban - self.position) % 4
            }
        })

    def skip(self):
        self.last_action.append({
            'type': 'skip'
        })

    def __able_richi(self):
        return (not [h['type'] != 0 for h in self.huro]) and calc_shanten(self.tehai, len(self.huro))

    def __able_kan(self):
        return any([all(self.tehai[i*4:i*4+4]) for i in range(34)])
