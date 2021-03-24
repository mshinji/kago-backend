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
    PON_NETWORK = L.Classifier(CNN(n_output=2))
    CHI_NETWORK = L.Classifier(CNN(n_output=4))
    serializers.load_npz(os.path.join(module_dir, 'networks/dahai.npz'), DAHAI_NETWORK)
    serializers.load_npz(os.path.join(module_dir, 'networks/richi.npz'), RICHI_NETWORK)
    serializers.load_npz(os.path.join(module_dir, 'networks/pon.npz'), PON_NETWORK)
    serializers.load_npz(os.path.join(module_dir, 'networks/chi.npz'), CHI_NETWORK)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'kago'

    def make_input(self):
        # 手牌
        tehai = [0] * 34
        for pai in self.tehai:
            tehai[pai//4] += 1
        # 河
        kawa = [[0] * 34 for _ in range(4)]
        for i, (_, player) in enumerate(self.prange()):
            for pai in player.kawa:
                kawa[i][pai//4] += 1
        # 副露
        huro = [[0] * 34 for _ in range(4)]
        # 最後の打牌
        last_dahai = [1 if self.game.last_dahai == i else 0 for i in range(34)]

        row = []
        row += tehai
        for i in range(4):
            row += kawa[i]
        for i in range(4):
            row += huro[i]
        row += last_dahai

        x = []
        for i in range(len(row) // 34):
            xx = []
            for j in range(34):
                xx.append([1 if row[i * 34 + j] >= k else 0 for k in range(1, 5)])
            x.append(xx)

        x = np.array([x], np.float32)
        return x

    def decide_richi(self):
        if not any([self.can_richi(dahai) for dahai in self.tehai]):
            return False

        x = self.make_input()
        y = Kago.RICHI_NETWORK.predictor(x)[0].array

        return bool(y[1] > y[0])

    def decide_ankan(self):
        return None

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

        print('KAGO PON', y, mk, last_dahai)
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

        print('KAGO CHI', y, mk, last_dahai)
        return mk

    def decide_dahai(self, richi):
        x = self.make_input()
        y = Kago.DAHAI_NETWORK.predictor(x)[0].array
        mk, mv = -1, -float('inf')

        for i in range(34):
            if y[i] > mv:
                for p in range(i * 4 + 3, i * 4 - 1, -1):
                    if p in self.tehai and self.can_dahai(p) and (not richi or self.can_richi(p)):
                        mk, mv = p, y[i]
                        break

        return mk
