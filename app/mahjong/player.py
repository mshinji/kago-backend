from itertools import combinations

from .game import Game
from .agari import Agari
from .shanten import calc_shanten


class Player():
    def __init__(self, player_id=None):
        self.id = player_id
        self.actions = {}

    # 汎用関数
    def prange(self):
        return [[i % 4, self.game.players[i % 4]] for i in range(self.position, self.position + 4)]

    def tsumoho(self):
        ba = [self.game.kyoku, self.game.honba, self.game.kyotaku, self.position, self.position]
        jokyo_yaku = self.get_jokyo_yaku()

        agari = Agari(self.tehai, self.huro, self.game.last_tsumo, ba, jokyo_yaku)
        yakus = []
        for i in range(len(Agari.YAKU)):
            if agari.yaku[i] > 0:
                yakus.append({'name': Agari.YAKU[i], 'han': agari.yaku[i]})

        doras = []
        uradoras = []
        for i in range(5):
            if i < self.game.n_dora:
                doras.append(self.game.dora[i])
                uradoras.append(self.game.dora[i+5])
            else:
                doras.append(self.game.make_dummy(self.game.dora[i]))
                uradoras.append(self.game.make_dummy(self.game.dora[i+5]))

        score_movements = agari.score_movements
        for i, score_movement in enumerate(score_movements):
            self.game.scores[i] += score_movement

        return {
            'yakus': yakus,
            'doras': doras,
            'uradoras': uradoras,
            'scores': self.game.scores,
            'scoreMovements': score_movements,
        }

    def tsumo(self, pai):
        self.tehai.append(pai)
        self.tehai.sort()
        self.game.last_tsumo = pai

    def dahai(self, pai, richi):
        # TODO 打牌とリーチ宣言の分離
        if richi:
            self.game.richi_declarations[self.position] = True
            self.richi_pc = self.game.pc
        self.tehai.pop(self.tehai.index(pai))
        self.kawa.append(pai)
        self.game.last_dahai = pai
        self.game.last_teban = self.game.teban
        self.game.pc += 1

    def richi_complete(self):
        self.game.scores[self.position] -= 1000
        self.game.richis[self.position] = True
        self.game.kyotaku += 1

    def ankan(self, pais):
        for i in pais:
            self.tehai.pop(self.tehai.index(i))
        self.huro.append({'type': 'ankan', 'pais': pais})
        self.game.n_kan += 1
        self.game.pc += 10

    def pon(self, pais, pai):
        for i in pais:
            if i != pai:
                self.tehai.pop(self.tehai.index(i))
        self.huro.append({'type': 'pon', 'pais': pais})
        self.game.teban = self.position
        self.game.pc += 10

    def chi(self, pais, pai):
        for i in pais:
            if i != pai:
                self.tehai.pop(self.tehai.index(i))
        self.huro.append({'type': 'chi', 'pais': pais})
        self.game.teban = self.position
        self.game.pc += 10

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

    def get_dora(self, pai):
        if pai // 4 in [8, 17, 26]:
            return pai // 4 - 8

        if pai // 4 == 30:
            return 27

        if pai // 4 == 33:
            return 31

        return pai // 4 + 1

    # TODO agari.pyに組み込む
    def get_jokyo_yaku(self):
        jokyo_yaku = [0] * 55
        zenpai = [0] * 34
        huro_types = []
        for pai in self.tehai:
            zenpai[pai // 4] += 1
        for huro in self.huro:
            for pai in huro['pais']:
                zenpai[pai // 4] += 1
            huro_types.append(huro['type'])

        # 門前自摸
        if len(huro_types) - huro_types.count('ankan') == 0 and self.game.teban == self.position:
            jokyo_yaku[Agari.YAKU.index('門前清自摸和')] += 1
        # 立直
        if self.game.richis[self.position] and not 0 <= self.richi_pc <= 3:
            jokyo_yaku[Agari.YAKU.index('立直')] += 1
        # 一発
        if self.game.richis[self.position] and self.game.pc - self.richi_pc <= 4:
            jokyo_yaku[Agari.YAKU.index('一発')] += 1
        # TODO 槍槓
        # TODO 嶺上開花
        # 海底摸月
        if self.game.teban == self.position and len(self.game.yama) == 0:
            jokyo_yaku[Agari.YAKU.index('海底摸月')] += 1
        # 河底撈魚
        if self.game.teban != self.position and len(self.game.yama) == 0:
            jokyo_yaku[Agari.YAKU.index('河底撈魚')] += 1
        # 両立直
        if self.game.richis[self.position] and 0 <= self.richi_pc <= 3:
            jokyo_yaku[Agari.YAKU.index('両立直')] += 2
        # 天和
        if self.game.pc == 0:
            jokyo_yaku[Agari.YAKU.index('天和')] += 13
        # 地和
        if 1 <= self.game.pc <= 3:
            jokyo_yaku[Agari.YAKU.index('地和')] += 13
        # ドラ/裏ドラ
        for i in range(self.game.n_dora):
            jokyo_yaku[Agari.YAKU.index('ドラ')] += zenpai[self.get_dora(self.game.dora[i])]
            jokyo_yaku[Agari.YAKU.index('裏ドラ')] += zenpai[self.get_dora(self.game.dora[i + 5])]
        # 赤ドラ
        for pai in [16, 52, 88]:
            jokyo_yaku[Agari.YAKU.index('赤ドラ')] += self.tehai.count(pai)

        return jokyo_yaku

    # アクション判定関数
    def can_tsumoho(self):
        if self.game.teban != self.position:
            print('手番じゃない')
            return False
        # TODO calc_chantenの方をこっちに合わせる
        tehai = [0] * 136
        for i in self.tehai:
            tehai[i] += 1
        if calc_shanten(tehai, len(self.huro)) >= 0:
            print('和了ってない')
            return False

        # TODO パオ
        ba = [self.game.kyoku, self.game.honba, self.game.kyotaku, self.position, self.position]
        jokyo_yaku = self.get_jokyo_yaku()
        print('得点移動', Agari(self.tehai, self.huro, self.game.last_tsumo, ba, jokyo_yaku).score_movements)
        if Agari(self.tehai, self.huro, self.game.last_tsumo, ba, jokyo_yaku).score_movements == [0, 0, 0, 0]:
            print('役無し')
            return False

        return True

    def can_dahai(self, dahai):
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
        if len(self.game.yama) <= 0:
            # print('山に牌が1つ以上')
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

    # アクション関数
    def my_start_game(self):
        pass

    def start_kyoku_message(self):
        self.actions.append({
            'type': 'start_kyoku_message',
            'body': self.game_info()
        })

    def tsumoho_message(self, tsumoho):
        tsumoho = tsumoho.copy()
        tsumoho['scores'] = [tsumoho['scores'][i] for i, _ in self.prange()]
        tsumoho['scoreMovements'] = [tsumoho['scoreMovements'][i] for i, _ in self.prange()]

        self.actions.append({
            'type': 'tsumoho_message',
            'body': tsumoho
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

    def richi_complete_message(self):
        self.actions.append({
            'type': 'richi_complete_message',
            'body': {
                'scores': [self.game.scores[i % 4] for i in range(self.position, self.position + 4)],
                'richis': [self.game.richis[i % 4] for i in range(self.position, self.position + 4)]
            }
        })

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

    # 通知1(ツモ和/リーチ/暗槓/加槓)
    def tsumoho_notice_message(self):
        if self.can_tsumoho():
            self.actions.append({'type': 'tsumoho_notice_message'})

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

    # 通知2(ロン和/明槓/ポン/チー)
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
