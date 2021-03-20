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
        self.game.n_kan += 1

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
        if self.game.state != Game.NOTICE1_RECIEVE_STATE and self.game.state != Game.DAHAI_STATE:
            print('ステートがカンでも打牌でもない')
            return False
        if dahai not in self.tehai:
            print('手牌に打牌する牌がない')
            return False

        return True

    def can_ankan(self, ankan):
        if self.game.teban != self.position:
            print('手番じゃない')
            return False
        if self.game.state != Game.NOTICE1_SEND_STATE and self.game.state != Game.NOTICE1_RECIEVE_STATE:
            print('ステートがカンじゃない')
            return False
        if self.game.n_kan >= 4:
            print('カンの個数が4以上')
            return False
        if len(ankan) != 4:
            print('牌の数が4つじゃない')
            return False
        if len(set(ankan)) != 4:
            print('牌番号に同じものがある')
            return False
        if len(set([i // 4 for i in ankan])) != 1:
            print('牌を4で割った商が全て同じじゃない')
            return False
        print('tehai', self.tehai)
        for i in ankan:
            if i not in self.tehai:
                print('手牌に含まれていない牌がある')
                return False
        return True

    # def can_chi(self, chi):

    # アクション記録関数
    def my_start_game(self):
        pass

    def my_start_kyoku(self):
        self.actions.append({
            'type': 'start_kyoku',
            'body': self.game_info()
        })

    def my_tsumo(self, pai):
        self.actions.append({
            'type': 'my_tsumo',
            'body': {
                'pai': pai,
                'rest': len(self.game.yama)
            }
        })

    def other_tsumo(self, pai):
        self.actions.append({
            'type': 'other_tsumo',
            'body': {
                'dummy': self.game.make_dummy(pai),
                'who': (self.game.teban - self.position) % 4,
                'rest': len(self.game.yama)
            }
        })

    def my_ankan_notice(self):
        action = {
            'type': 'my_ankan_notice',
            'body': []
        }

        for i in range(34):
            if self.can_ankan([i * 4 + j for j in range(4)]):
                action['body'].append({
                    'pais': [i * 4 + j for j in range(4)],
                    'dummies': self.game.make_dummies([i * 4 + j for j in range(4)])
                })

        if len(action['body']) != 0:
            self.actions.append(action)

    def my_ankan(self, pais):
        self.actions.append({
            'type': 'my_ankan',
            'body': {
                'pais': pais,
                'dummies': self.game.make_dummies(pais)
            }
        })

    def other_ankan(self, pais):
        self.actions.append({
            'type': 'other_ankan',
            'body': {
                'pais': pais,
                'dummies': self.game.make_dummies(pais),
                'who': (self.game.teban - self.position) % 4,
            }
        })

    def all_open_kan_dora(self, pai):
        self.actions.append({
            'type': 'all_open_kan_dora',
            'body': {
                'pai': pai,
                'dummy': self.game.make_dummy(pai),
                'rest': len(self.game.yama)
            }
        })

    def my_dahai(self, pai):
        self.actions.append({
            'type': 'my_dahai',
            'body': {
                'pai': pai
            }
        })

    def other_dahai(self, pai):
        self.actions.append({
            'type': 'other_dahai',
            'body': {
                'pai': pai,
                'dummy': self.game.make_dummy(pai),
                'who': (self.game.teban - self.position) % 4
            }
        })

    # def my_chi_notice(self, dahai):
    #     action = {
    #         'type': 'my_chi_notice',
    #         'body': {'pais': []}
    #     }

    #     for i in range(34):
    #         if self.can_chi([i * 4 + j for j in range(4)]):
    #             action['body']['pais'].append({
    #                 'pai': [i * 4 + j for j in range(4)],
    #                 'dummy': self.game.make_dummies([i * 4 + j for j in range(4)])
    #             })

    #     if len(action['body']['pais']) != 0:
    #         self.actions.append(action)

        # def other_huro_notice(self, dahai):
