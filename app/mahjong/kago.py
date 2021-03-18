import os

import chainer.links as L
import numpy as np
from chainer import serializers

from mahjong.cnn import CNN
from mahjong.player import Player

module_dir = os.path.dirname(__file__)


class Kago(Player):
    DAHAI_NETWORK = L.Classifier(CNN(n_output=34))
    serializers.load_npz(os.path.join(module_dir, 'networks/dahai.npz'), DAHAI_NETWORK)

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

    def decide_ankan(self):
        return None

    def decide_dahai(self):
        x = self.make_input()
        y = Kago.DAHAI_NETWORK.predictor(x)[0].array
        mk, mv = -1, -float('inf')
        tehai = [0] * 34
        for pai in self.tehai:
            tehai[pai//4] += 1

        for i in range(34):
            if tehai[i] > 0 and y[i] > mv:
                mk, mv = i, y[i]

        print('tehai:', tehai)
        print('result:', mk)
        for i in range(4):
            if mk * 4 + i in self.tehai:
                dahai = self.tehai.pop(self.tehai.index(mk * 4 + i))
                break
        self.kawa.append(dahai)
        return dahai
