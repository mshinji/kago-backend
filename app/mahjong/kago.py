import os

import chainer.links as L
import numpy as np
from chainer import serializers

from mahjong.cnn import CNN
from mahjong.player import Player

module_dir = os.path.dirname(__file__)


class Kago(Player):
    DAHAI_NETWORK = L.Classifier(CNN())
    serializers.load_npz(os.path.join(module_dir, 'dahai_network.npz'), DAHAI_NETWORK)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'kago'

    def dahai(self):
        tehai = [0] * 34
        for pai in self.tehai:
            tehai[pai//4] += 1

        kawa = [[0] * 34 for _ in range(4)]
        for i, who in enumerate(self.prange()):
            for pai in self.game.players[who].kawa:
                kawa[who][pai//4] += 1

        huro = [[0] * 34 for _ in range(4)]

        row = []
        row += tehai
        for i in range(4):
            row += kawa[i]
            row += huro[i]

        x = []
        for i in range(9):
            xx = []
            for j in range(34):
                xx.append([1 if row[i * 34 + j] >= k else 0 for k in range(1, 5)])
            x.append(xx)

        x = np.array([x], np.float32)
        y = Kago.DAHAI_NETWORK.predictor(x)[0].array
        mk, mv = -1, -float('inf')
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
