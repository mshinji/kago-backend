from .game import Game


class Player():
    def __init__(self, player_id=None):
        self.id = player_id
        self.actions = {}

    # 汎用関数
    def prange(self):
        return [[i % 4, self.game.players[i % 4]] for i in range(self.position, self.position + 4)]

    def tsumo(self):
        tsumo = self.game.yama.pop()
        self.tehai.append(tsumo)
        self.tehai.sort()
        return tsumo

    def dahai(self, pai):
        self.tehai.pop(self.tehai.index(pai))
        self.kawa.append(pai)

    def ankan(self, ankan):
        for i in ankan:
            self.tehai.pop(self.tehai.index(i))
        self.huro.append(ankan)

    def reset_actions(self):
        self.actions = []

    def game_info(self):
        tehais = []
        for i, player in self.prange():
            if i == self.position:
                tehais.append(player.tehai)
            else:
                tehais.append(self.game.make_dummies(player.tehai))

        kawas = []
        for i, player in self.prange():
            if i == self.position:
                kawas.append(player.kawa)
            else:
                kawas.append(self.game.make_dummies(player.kawa))

        huros = []
        for _, player in self.prange():
            huros.append(player.huro)

        dora = self.game.dora[:self.game.n_dora] + self.game.make_dummies(self.game.dora[self.game.n_dora:5])

        scores = [self.game.scores[i] for i, _ in self.prange()]
        richis = [self.game.richis[i] for i, _ in self.prange()]
        kazes = ['東南西北'[(i - self.game.kyoku) % 4] for i, _ in self.prange()]
        rest = len(self.game.yama)

        return {
            'tehais': tehais,
            'kawas': kawas,
            'huros': huros,
            'kyoku': self.game.kyoku,
            'honba': self.game.honba,
            'kyotaku': self.game.kyotaku,
            'dora': dora,
            'rest': rest,
            'scores': scores,
            'richis': richis,
            'kazes': kazes,
        }

    # アクション判定関数
    def can_dahai(self, dahai):
        if self.game.teban != self.position:
            print('手番じゃない')
            return False
        if self.game.state != Game.KAN_STATE and self.game.state != Game.DAHAI_STATE:
            print('ステートがカンでも打牌じゃない')
            return False
        if dahai not in self.tehai:
            print('手牌に打牌する牌がない')
            return False

        return True

    def can_ankan(self, ankan):
        if self.game.teban != self.position:
            print('手番じゃない')
            return False
        if self.game.state != Game.KAN_STATE:
            print('ステートがカンじゃない')
            return False
        if len(ankan) != 4:
            print('牌の数が4つじゃない')
            return False
        if len(set(ankan)) != 4:
            print('牌番号に同じものがある')
            return False
        if len(set([i // 4 for i in ankan])) != 1:
            print('牌を4で割った商が全て同じ')
            return False
        print('tehai', self.tehai)
        for i in ankan:
            if i not in self.tehai:
                print('手牌に含まれていない牌がある')
                return False
        return True

    # アクション記録関数
    def my_start_game(self):
        pass

    def my_start_kyoku(self):
        self.actions.append({
            'type': 'start_kyoku',
            'body': self.game_info()
        })

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

    def all_open_kan_dora(self, kan_dora):
        self.actions.append({
            'type': 'all_open_kan_dora',
            'body': {
                'pai': kan_dora,
                'dummy': self.game.make_dummy(kan_dora),
                'rest': len(self.game.yama)
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
