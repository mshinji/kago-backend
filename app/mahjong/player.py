from .shanten import calc_shanten


class Player():
    def __init__(self, player_id=None):
        self.id = player_id
        self.actions = {}

    def prange(self):
        return [i % 4 for i in range(self.position, self.position + 4)]

    def reset_actions(self):
        self.actions = []

    def start_game(self):
        pass

    def start_kyoku(self):
        self.tehai = []
        self.huro = []
        self.kawa = []

    def tsumo(self, pai):
        self.tehai.append(pai)
        self.tehai.sort()

    # アクション可能判定関数
    def can_dahai(self, dahai):
        return dahai in self.tehai[dahai]

    def can_ankan(self, ankan):
        # 牌の数が4つじゃない
        if len(ankan) != 4:
            return False
        # 牌番号に同じものがある
        if len(set(ankan)) != 4:
            return False
        # 牌を4で割った商が全て同じ
        if len(set([i // 4 for i in ankan])) != 1:
            return False
        print('tehai', self.tehai)
        # 手牌に含まれていない牌がある
        for i in ankan:
            if i not in self.tehai:
                return False
        print('True')
        return True

    # アクション記録関数群
    def my_tsumo(self, tsumo):
        self.actions.append({
            'type': 'my_tsumo',
            'body': {
                'tsumo': tsumo,
                'rest': len(self.game.yama)
            }
        })

    def other_tsumo(self, tsumo):
        self.actions.append({
            'type': 'other_tsumo',
            'body': {
                'tsumo': self.game.make_dummy(tsumo),
                'who': (self.game.teban - self.position) % 4,
                'rest': len(self.game.yama)
            }
        })

    def my_before_ankan(self):
        action = {
            'type': 'my_before_ankan',
            'body': {'ankan': []}
        }

        x = [0] * 34
        for t in self.tehai:
            x[t//4] += 1
        print(x)

        for i in range(34):
            if x[i] >= 4:
                action['body']['ankan'].append({
                    'pai': [i * 4 + j for j in range(4)],
                    'dummy': self.game.make_dummies([i * 4 + j for j in range(4)])
                })

        if len(action['body']['ankan']) != 0:
            self.actions.append(action)

    def my_ankan(self, ankan):
        self.actions.append({
            'type': 'my_ankan',
            'body': {
                'pai': ankan,
                'dummy': self.game.make_dummies(ankan)
            }
        })

    def other_ankan(self, ankan):
        self.actions.append({
            'type': 'other_ankan',
            'body': {
                'pai': ankan,
                'dummy': self.game.make_dummies(ankan),
                'who': (self.game.teban - self.position) % 4,
            }
        })

    def my_dahai(self, dahai):
        self.actions.append({
            'type': 'my_dahai',
            'body': {
                'dahai': dahai
            }
        })

    def other_dahai(self, dahai):
        self.actions.append({
            'type': 'other_dahai',
            'body': {
                'dahai': dahai,
                'dummy': self.game.make_dummy(dahai),
                'who': (self.game.teban - self.position) % 4
            }
        })

    def skip(self):
        self.actions.append({
            'type': 'skip'
        })

    def __able_richi(self):
        return (not [h['type'] != 0 for h in self.huro]) and calc_shanten(self.tehai, len(self.huro))

    def __able_kan(self):
        return any([all(self.tehai[i*4:i*4+4]) for i in range(34)])
