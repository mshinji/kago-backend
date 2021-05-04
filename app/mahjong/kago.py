import os
from itertools import product

import chainer.links as L
import numpy as np
from chainer import serializers

from mahjong.cnn import CNN
from mahjong.player import Player

module_dir = os.path.dirname(__file__)


class Kago(Player):
    DAHAI_NETWORK = L.Classifier(CNN(n_output=34))
    RICHI_NETWORK = L.Classifier(CNN(n_output=2))
    ANKAN_NETWORK = L.Classifier(CNN(n_output=2))
    PON_NETWORK = L.Classifier(CNN(n_output=2))
    CHI_NETWORK = L.Classifier(CNN(n_output=4))
    serializers.load_npz(os.path.join(module_dir, 'networks/dahai.npz'), DAHAI_NETWORK)
    serializers.load_npz(os.path.join(module_dir, 'networks/richi.npz'), RICHI_NETWORK)
    serializers.load_npz(os.path.join(module_dir, 'networks/ankan.npz'), ANKAN_NETWORK)
    serializers.load_npz(os.path.join(module_dir, 'networks/pon.npz'), PON_NETWORK)
    serializers.load_npz(os.path.join(module_dir, 'networks/chi.npz'), CHI_NETWORK)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'kago'

    def make_input(self):
        # 手牌
        tehai = [0] * 34
        for pai in self.tehai:
            tehai[pai // 4] += 1

        # 赤
        aka = [0] * 34
        for pai in self.tehai:
            if pai in [16, 52, 88]:
                aka[pai // 4] = 4

        # 河
        kawa = [[0] * 34 for _ in range(4)]
        for i, (_, player) in enumerate(self.prange()):
            for pai in player.kawa:
                kawa[i][pai // 4] += 1

        # 副露
        huro = [[0] * 34 for _ in range(4)]
        for i, (_, player) in enumerate(self.prange()):
            for h in player.huro:
                for pai in h['pais']:
                    huro[i][pai // 4] += 1
        # ドラ
        dora = [0] * 34
        for pai in self.game.dora[:self.game.n_dora]:
            dora[pai // 4] += 1

        # リーチ
        richi = [[0] * 34 for _ in range(3)]
        for i, (_, player) in enumerate(self.prange()[1:]):
            if player.richi_pai is not None:
                richi[i][player.richi_pai // 4] = 4

        # 場風
        bakaze = [0] * 34
        bakaze[27 + self.game.kyoku // 4] = 4

        # 自風
        zikaze = [0] * 34
        zikaze[27 + (self.position - self.game.kyoku) % 4] = 4

        # 最後の打牌
        last_dahai = [0] * 34
        if self.game.last_dahai is not None:
            last_dahai[self.game.last_dahai // 4] = 4

        row = []
        row += tehai
        row += aka
        for i in range(4):
            row += kawa[i]
        for i in range(4):
            row += huro[i]
        row += dora
        for i in range(3):
            row += richi[i]
        row += bakaze
        row += zikaze
        row += last_dahai

        x = []
        for i in range(len(row) // 34):
            xx = []
            for j in range(34):
                xx.append([1 if row[i * 34 + j] >= k else 0 for k in range(1, 5)])
            x.append(xx)

        x = np.array([x], np.float32)
        return x

    def debug(self, x):
        jp = ['1m', '2m', '3m', '4m', '5m', '6m', '7m', '8m', '9m',
              '1p', '2p', '3p', '4p', '5p', '6p', '7p', '8p', '9p',
              '1s', '2s', '3s', '4s', '5s', '6s', '7s', '8s', '9s',
              '東', '南', '西', '北', '白', '発', '中', '-']

        data = x[0]
        for i, plate in enumerate(data):
            if i == 0:
                print('====================')
                print('手牌')
            if i == 1:
                print('====================')
                print('赤牌')
            if i == 2:
                print('====================')
                print('河')
            if i == 6:
                print('====================')
                print('副露')
            if i == 10:
                print('====================')
                print('ドラ')
            if i == 11:
                print('====================')
                print('リーチ')
            if i == 14:
                print('====================')
                print('場風')
            if i == 15:
                print('====================')
                print('自風')
            if i == 16:
                print('====================')
                print('最後の打牌')

            detail = ''
            for j, row in enumerate(plate):
                for p in row:
                    if p == 1:
                        detail += jp[j]
            print(detail)

    def decide_tsumoho(self):
        if self.can_tsumoho():
            return True
        else:
            return False

    def decide_ankan(self):
        x = self.make_input()
        y = Kago.ANKAN_NETWORK.predictor(x)[0].array
        mk, mv = None, -float('inf')

        for i in range(2):
            if y[i] > mv:
                if i == 0:
                    mk, mv = None, y[i]
                if i == 1:
                    for p in range(34):
                        if self.can_ankan([p * 4, p * 4 + 1, p * 4 + 2, p * 4 + 3]):
                            mk, mv = [p * 4, p * 4 + 1, p * 4 + 2, p * 4 + 3], y[i]
                            break

        return mk

    def decide_richi(self):
        if not any([self.can_richi_declare(dahai) for dahai in self.tehai]):
            return False

        x = self.make_input()
        y = Kago.RICHI_NETWORK.predictor(x)[0].array

        return bool(y[1] > y[0])

    def decide_dahai(self):
        x = self.make_input()
        y = Kago.DAHAI_NETWORK.predictor(x)[0].array
        mk, mv = -1, -float('inf')

        for i in range(34):
            if y[i] < mv:
                continue
            for p in range(i * 4 + 3, i * 4 - 1, -1):
                if p in self.tehai and self.can_dahai(p):
                    mk, mv = p, y[i]
                    break

        return mk

    def decide_ronho(self):
        if self.can_ronho():
            return True
        else:
            return False

    def decide_pon(self):
        x = self.make_input()
        y = Kago.PON_NETWORK.predictor(x)[0].array
        mk, mv = None, -float('inf')

        last_dahai = self.game.last_dahai
        for i in range(2):
            if y[i] > mv:
                if i == 0:
                    mk, mv = None, y[i]
                if i == 1:
                    p = last_dahai // 4 * 4
                    for a, b in product(range(p, p + 4), range(p, p + 4)):
                        if a == b or b == last_dahai or last_dahai == a:
                            continue
                        if self.can_pon([last_dahai, a, b], last_dahai):
                            mk, mv = [last_dahai, a, b], y[i]
                            break

        return mk

    def decide_chi(self):
        x = self.make_input()
        y = Kago.CHI_NETWORK.predictor(x)[0].array
        mk, mv = None, -float('inf')

        last_dahai = self.game.last_dahai
        for i in range(4):
            if y[i] > mv:
                if i == 0:
                    mk, mv = None, y[i]
                if i == 1:
                    p1 = (last_dahai // 4 + 1) * 4
                    p2 = (last_dahai // 4 + 2) * 4
                    for a, b in product(range(p1, p1 + 4), range(p2, p2 + 4)):
                        if self.can_chi([last_dahai, a, b], last_dahai):
                            mk, mv = [last_dahai, a, b], y[i]
                            break
                if i == 2:
                    p1 = (last_dahai // 4 - 1) * 4
                    p2 = (last_dahai // 4 + 1) * 4
                    for a, b in product(range(p1, p1 + 4), range(p2, p2 + 4)):
                        if self.can_chi([last_dahai, a, b], last_dahai):
                            mk, mv = [last_dahai, a, b], y[i]
                            break
                if i == 3:
                    p1 = (last_dahai // 4 - 2) * 4
                    p2 = (last_dahai // 4 - 1) * 4
                    for a, b in product(range(p1, p1 + 4), range(p2, p2 + 4)):
                        if self.can_chi([last_dahai, a, b], last_dahai):
                            mk, mv = [last_dahai, a, b], y[i]
                            break

        return mk
