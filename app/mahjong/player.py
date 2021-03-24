from itertools import combinations

from .game import Game
from .shanten import calc_shanten


class Player():
    def __init__(self, player_id=None):
        self.id = player_id
        self.actions = {}

    # 汎用関数
    def prange(self):
        return [[i % 4, self.game.players[i % 4]] for i in range(self.position, self.position + 4)]

    def tsumo(self, pai):
        self.tehai.append(pai)
        self.tehai.sort()
        self.game.last_tsumo = pai

    def dahai(self, pai, richi):
        # TODO リーチ処理
        if richi:
            self.game.richis[self.position] = True
        self.tehai.pop(self.tehai.index(pai))
        self.kawa.append(pai)
        self.game.last_dahai = pai
        self.game.last_teban = self.game.teban

    def ankan(self, pais):
        for i in pais:
            self.tehai.pop(self.tehai.index(i))
        self.huro.append({'type': 'ankan', 'pais': pais})
        self.game.n_kan += 1

    def pon(self, pais, pai):
        for i in pais:
            if i != pai:
                self.tehai.pop(self.tehai.index(i))
        self.huro.append({'type': 'pon', 'pais': pais})
        self.game.teban = self.position

    def chi(self, pais, pai):
        for i in pais:
            if i != pai:
                self.tehai.pop(self.tehai.index(i))
        self.huro.append({'type': 'chi', 'pais': pais})
        self.game.teban = self.position

    def cancel(self):
        self.game.minkan_dicisions[self.position] = [None, None]
        self.game.pon_dicisions[self.position] = [None, None]
        self.game.chi_dicisions[self.position] = [None, None]

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

        richi_declaration_pais = []
        for player in self.game.players:
            if player.richi_declaration_pai is not None:
                richi_declaration_pais.append(player.richi_declaration_pai)

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
            'richiDeclarationPais': richi_declaration_pais,
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
        print('RICHIS:', self.game.richis, self.position)
        if self.game.teban != self.position:
            # print('手番じゃない')
            return False
        if self.game.state != Game.NOTICE1_RECIEVE_STATE and self.game.state != Game.DAHAI_STATE:
            # print('ステートがカンでも打牌でもない')
            return False
        if dahai not in self.tehai:
            # print('手牌に打牌する牌がない')
            return False
        if self.game.richis[self.position] and dahai != self.game.last_tsumo:
            # print('リーチ後にツモ切りしてない')
            return False

        return True

    def can_richi(self, dahai):
        if self.game.teban != self.position:
            # print('手番じゃない')
            return False
        if self.game.richis[self.position]:
            # print('リーチしている')
            return False
        if self.game.state not in [Game.NOTICE1_SEND_STATE, Game.NOTICE1_RECIEVE_STATE, Game.DAHAI_STATE]:
            # print('ステート異常')
            return False
        huro_types = [huro['type'] for huro in self.huro]
        if len(huro_types) - huro_types.count('ankan') != 0:
            # print('門前じゃない')
            return False
        # TODO 1000点以上ない

        tehai = [0] * 136
        for i in self.tehai:
            if i != dahai:
                tehai[i] += 1
        if calc_shanten(tehai, len(self.huro)) >= 1:
            # print('テンパってない')
            return False

        return True

    def can_ankan(self, ankan):
        if self.game.teban != self.position:
            # print('手番じゃない')
            return False
        if self.game.state != Game.NOTICE1_SEND_STATE and self.game.state != Game.NOTICE1_RECIEVE_STATE:
            # print('ステートがカンじゃない')
            return False
        if self.game.n_kan >= 4:
            # print('カンの個数が4以上')
            return False
        if len(ankan) != 4:
            # print('牌の数が4つじゃない')
            return False
        if len(set(ankan)) != 4:
            # print('牌番号に同じものがある')
            return False
        if len(set([i // 4 for i in ankan])) != 1:
            # print('牌を4で割った商が全て同じじゃない')
            return False
        for i in ankan:
            if i not in self.tehai:
                # print('手牌に含まれていない牌がある')
                return False
        return True

    def can_pon(self, pais, pai):
        if self.game.teban == self.position:
            # print('捨てた本人')
            return False
        if self.game.richis[self.position]:
            # print('リーチしている')
            return False
        if self.game.state != Game.NOTICE2_SEND_STATE and self.game.state != Game.NOTICE2_RECIEVE_STATE:
            # print('ステート異常')
            return False
        if pai not in pais:
            # print('鳴いた牌が含まれていない')
            return False
        if self.game.last_dahai != pai:
            # print('鳴いた牌が最後の打牌と不一致')
            return False
        if len(pais) != 3:
            # print('牌の数が3つじゃない')
            return False
        for i in range(3):
            if pais[i] != pai and pais[i] not in self.tehai:
                # print('手牌に含まれていない牌がある')
                return False
        if not pais[0] // 4 == pais[1] // 4 == pais[2] // 4:
            # print('同じじゃない', pais, pai, self.tehai)
            return False
        if len(set(pais)) != 3:
            # print('牌番号に同じものがある')
            return False
        print('pon', pais)
        return True

    def can_chi(self, pais, pai):
        if (self.game.teban + 1) % 4 != self.position:
            # print('次の手番じゃない')
            return False
        if self.game.richis[self.position]:
            # print('リーチしている')
            return False
        if self.game.state != Game.NOTICE2_SEND_STATE and self.game.state != Game.NOTICE2_RECIEVE_STATE:
            # print('ステート異常')
            return False
        if pai not in pais:
            # print('鳴いた牌が含まれていない')
            return False
        if self.game.last_dahai != pai:
            # print('鳴いた牌が最後の打牌と不一致')
            return False
        if len(pais) != 3:
            # print('牌の数が3つじゃない')
            return False
        for i in range(3):
            if pais[i] != pai and pais[i] not in self.tehai:
                # print('手牌に含まれていない牌がある')
                return False
        pais.sort()
        if pais[2] // 4 - pais[1] // 4 != 1 or pais[1] // 4 - pais[0] // 4 != 1:
            # print('連続していない', pais, pai)
            return False
        if pais[0] >= 4 * 27:
            # print('字牌')
            return False
        if pais[0] // (4 * 9) != pais[2] // (4 * 9):
            # print('複数の種類の牌がある')
            return False
        if len(set(pais)) != 3:
            # print('牌番号に同じものがある')
            return False
        print('chi', pais)
        return True

    # アクション記録関数
    def my_start_game(self):
        pass

    def start_kyoku_message(self):
        self.actions.append({
            'type': 'start_kyoku_message',
            'body': self.game_info()
        })

    def tsumo_message(self, pai):
        data = {
            'type': 'tsumo_message',
            'body': {
                    'who': (self.game.teban - self.position) % 4,
                    'rest': len(self.game.yama)
            }
        }

        if self.game.teban == self.position:
            data['body']['pai'] = pai
        else:
            data['body']['dummy'] = self.game.make_dummy(pai)

        self.actions.append(data)

    def richi_notice_message(self):
        action = {
            'type': 'richi_notice_message',
            'body': []
        }

        for i in self.tehai:
            if self.can_richi(i):
                action['body'].append({
                    'pai': i,
                })

        if len(action['body']) != 0:
            self.actions.append(action)

    def ankan_notice_message(self):
        action = {
            'type': 'ankan_notice_message',
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

    def ankan_message(self, pais):
        self.actions.append({
            'type': 'ankan_message',
            'body': {
                'pais': pais,
                'dummies': self.game.make_dummies(pais),
                'who': (self.game.teban - self.position) % 4,
                'fromWho': (self.game.teban - self.position) % 4
            }
        })

    def pon_notice_message(self):
        action = {
            'type': 'pon_notice_message',
            'body': []
        }

        done = [[0] * 2 for _ in range(34)]
        aka = [16, 52, 88]
        for i, j in combinations(self.tehai, 2):
            if not i // 4 == j // 4 == self.game.last_dahai // 4:
                continue

            if i in aka or j in aka or self.game.last_dahai in aka:
                if done[i//4][1] == 0:
                    pais = [self.game.last_dahai, i, j]
                    if self.can_pon(pais, self.game.last_dahai):
                        action['body'].append({
                            'pai': self.game.last_dahai,
                            'pais': pais,
                            'dummies': self.game.make_dummies(pais),
                            'fromWho': (self.game.last_teban - self.position) % 4
                        })
                        done[i//4][1] = 1
            else:
                if done[i//4][0] == 0:
                    pais = [self.game.last_dahai, i, j]
                    if self.can_pon(pais, self.game.last_dahai):
                        action['body'].append({
                            'pai': self.game.last_dahai,
                            'pais': pais,
                            'dummies': self.game.make_dummies(pais),
                            'fromWho': (self.game.last_teban - self.position) % 4
                        })
                        done[i//4][0] = 1

        if len(action['body']) == 0:
            self.game.pon_dicisions[self.position] = [None, None]
        else:
            self.actions.append(action)

    def pon_message(self, pais, pai):
        self.actions.append({
            'type': 'pon_message',
            'body': {
                'pai': pai,
                'pais': pais,
                'dummies': self.game.make_dummies(pais),
                'who': (self.game.teban - self.position) % 4,
                'fromWho': (self.game.last_teban - self.position) % 4
            }
        })

    def chi_notice_message(self):
        action = {
            'type': 'chi_notice_message',
            'body': []
        }

        tmp = set(map(self.game.make_simple, self.tehai))
        tehai = []
        for i in self.tehai:
            if self.game.make_simple(i) in tmp:
                tehai.append(i)
                tmp.remove(self.game.make_simple(i))

        for i, j in combinations(tehai, 2):
            pais = [self.game.last_dahai, i, j]
            if self.can_chi(pais, self.game.last_dahai):
                action['body'].append({
                    'pai': self.game.last_dahai,
                    'pais': pais,
                    'dummies': self.game.make_dummies(pais),
                    'fromWho': (self.game.last_teban - self.position) % 4
                })

        if len(action['body']) == 0:
            self.game.chi_dicisions[self.position] = [None, None]
        else:
            self.actions.append(action)

    def chi_message(self, pais, pai):
        self.actions.append({
            'type': 'chi_message',
            'body': {
                'pai': pai,
                'pais': pais,
                'dummies': self.game.make_dummies(pais),
                'who': (self.game.teban - self.position) % 4,
                'fromWho': (self.game.last_teban - self.position) % 4
            }
        })

    def open_dora_message(self, pai):
        self.actions.append({
            'type': 'open_dora_message',
            'body': {
                'pai': pai,
                'dummy': self.game.make_dummy(pai),
                'rest': len(self.game.yama)
            }
        })

    def dahai_message(self, pai, richi):
        self.actions.append({
            'type': 'dahai_message',
            'body': {
                'pai': pai,
                'dummy': self.game.make_dummy(pai),
                'who': (self.game.teban - self.position) % 4,
                'richi': richi
            }
        })
