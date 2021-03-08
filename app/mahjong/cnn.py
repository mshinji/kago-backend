import chainer.functions as F
import chainer.links as L
from chainer import Chain


class CNN(Chain):
    def __init__(self, n_output):
        super(CNN, self).__init__()
        with self.init_scope():
            ksize = (5, 2)
            self.conv1 = L.Convolution2D(in_channels=None, out_channels=100, ksize=ksize)
            self.conv2 = L.Convolution2D(in_channels=None, out_channels=100, ksize=ksize)
            self.conv3 = L.Convolution2D(in_channels=None, out_channels=100, ksize=ksize)
            self.bnorm1 = L.BatchNormalization(100)
            self.bnorm2 = L.BatchNormalization(100)
            self.bnorm3 = L.BatchNormalization(100)
            self.fc1 = L.Linear(None, 300)
            self.fc2 = L.Linear(None, n_output)

    def __call__(self, x):
        # 1層
        h = self.conv1(x)
        h = self.bnorm1(h)
        h = F.relu(h)
        h = F.dropout(h, ratio=0.5)
        # 2層
        h = self.conv2(h)
        h = self.bnorm2(h)
        h = F.relu(h)
        h = F.dropout(h, ratio=0.5)
        # 3層
        h = self.conv3(h)
        h = self.bnorm3(h)
        h = F.relu(h)
        h = F.dropout(h, ratio=0.5)
        # 平坦化
        h = h.reshape(-1, 2200)
        # 4層
        h = self.fc1(h)
        h = F.relu(h)
        h = F.dropout(h, ratio=0.5)
        # 5層
        h = self.fc2(h)
        return h
