import os
from itertools import product

import numpy as np
from tensorflow.keras import models

from .player import Player

module_dir = os.path.dirname(__file__)


class Kago(Player):
    DAHAI_NETWORK = models.load_model(os.path.join(module_dir, 'networks/dahai.h5'))
    RICHI_NETWORK = models.load_model(os.path.join(module_dir, 'networks/richi.h5'))
    ANKAN_NETWORK = models.load_model(os.path.join(module_dir, 'networks/ankan.h5'))
    PON_NETWORK = models.load_model(os.path.join(module_dir, 'networks/pon.h5'))
    CHI_NETWORK = models.load_model(os.path.join(module_dir, 'networks/chi.h5'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'kago'

    def make_input(self):
        row = []

        # 手牌
        tehai = [0] * 34
        for pai in self.tehai:
            tehai[pai // 4] += 1
        for i in range(1, 4 + 1):
            row += [1 if tehai[j] >= i else 0 for j in range(34)]

        # 赤
        row += [1] * 34 if 16 in self.tehai else [0] * 34
        row += [1] * 34 if 52 in self.tehai else [0] * 34
        row += [1] * 34 if 88 in self.tehai else [0] * 34

        # 河
        for _, player in self.prange():
            for i in range(20):
                tmp = [0] * 34
                if i < len(player.kawa):
                    tmp[player.kawa[i] // 4] = 1
                row += tmp

        # 副露
        for _, player in self.prange():
            huro = [0] * 34
            for h in player.huro:
                for pai in h['pais']:
                    huro[pai // 4] += 1
            for i in range(1, 4 + 1):
                row += [1 if huro[j] >= i else 0 for j in range(34)]

        # ドラ
        dora = [0] * 34
        for pai in self.game.dora[:self.game.n_dora]:
            dora[pai // 4] += 1
        for i in range(1, 4 + 1):
            row += [1 if dora[j] >= i else 0 for j in range(34)]

        # リーチ
        for _, player in self.prange():
            if player.richi_pai is not None:
                row += [1] * 34
            else:
                row += [0] * 34

        # 局数
        for i in range(12):
            if i == min(self.game.kyoku, 11):
                row += [1] * 34
            else:
                row += [0] * 34

        # 座順
        for i in range(4):
            if i == self.position:
                row += [1] * 34
            else:
                row += [0] * 34

        # データ準備
        n_channel = len(row) // 34
        x = [[[0] * n_channel for _ in range(34)]]
        for k, v in enumerate(row):
            x[0][k % 34][k // 34] = v

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
        y = Kago.ANKAN_NETWORK.predict(x)[0]
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
        y = Kago.RICHI_NETWORK.predict(x)[0]

        return bool(y[1] > y[0])

    def decide_dahai(self):
        x = self.make_input()
        y = Kago.DAHAI_NETWORK.predict(x)[0]
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
        y = Kago.PON_NETWORK.predict(x)[0]
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
        y = Kago.CHI_NETWORK.predict(x)[0]
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
