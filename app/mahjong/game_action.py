from random import shuffle

from .game_base import GameBase


class GameAction:
    def start_game(self):
        shuffle(self.players)
        for i, player in enumerate(self.players):
            player.position = i

        self.state = GameBase.KYOKU_START_STATE
        self.prev_state = GameBase.INITIAL_STATE

    def start_kyoku(self):
        # 各プレイヤーの手牌・河・副露の初期化
        for player in self.players:
            player.tehai = []
            player.kawa = []
            player.huro = []

            player.richi_pc = None
            player.richi_pai = None
            player.is_richi_declare = False
            player.is_richi_complete = False

        # 手番設定(最初は1引く)
        self.teban = (self.kyoku - 1) % 4

        # ダミーデータ生成
        self.dummy = [136 + i for i in range(136)]
        shuffle(self.dummy)

        # 山生成
        self.yama = [i for i in range(136)]
        shuffle(self.yama)

        # カン
        # original = [
        #     108 + 13, 108 + 14, 108 + 15, 108 + 16, 108 + 17,
        #     * list(range(0, 0 + 13)),
        #     *list(range(36, 36 + 13)),
        #     *list(range(72, 72 + 13)),
        #     *list(range(108, 108 + 13))
        # ]
        # チーしやすい
        # original = [
        #     0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48,
        #     1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49,
        #     2, 6, 10, 14, 18, 22, 26, 30, 34, 38, 42, 46, 50,
        #     3, 7, 11, 15, 19, 23, 27, 31, 35, 39, 43, 47, 51
        # ]
        # ポンしやすい
        # original = [
        #     108, 112, 116,
        #     0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 37, 76, 80,
        #     1, 5, 9, 13, 17, 21, 25, 29, 33, 40, 41, 77, 81,
        #     2, 6, 10, 14, 18, 22, 26, 30, 34, 44, 45, 78, 82,
        #     109, 110, 111, 113, 114, 115, 117, 118, 119, 120, 121, 122, 123,
        # ]
        # 上がりやすい
        # original = [
        #     0, 4, 8, 12, 16, 20, 21, 22, 24, 25, 124, 125, 126,
        #     36, 40, 44, 48, 52, 56, 57, 58, 60, 61, 128, 129, 130,
        #     72, 76, 80, 84, 88, 92, 93, 94, 96, 97, 132, 133, 134
        # ]
        # 国士無双13面
        # original = [0 * 4, 8 * 4, 9 * 4, 17 * 4, 18 * 4, 26 * 4] + [i for i in range(4 * 27, 4 * 34, 4)]

        # self.yama = [i for i in range(136)]
        # shuffle(self.yama)
        # for i in original:
        #     self.yama.pop(self.yama.index(i))
        # self.yama = self.yama[:len(self.yama)-14] + original + self.yama[len(self.yama)-14:]

        # ドラ生成
        self.dora = []
        for _ in range(10):
            self.dora.append(self.yama.pop())
        self.n_dora = 1

        # 嶺上生成
        self.rinshan = []
        for _ in range(4):
            self.rinshan.append(self.yama.pop())

        # 配牌
        for player in self.players:
            for _ in range(13):
                tsumo = self.yama.pop()
                player.tsumo(tsumo)

        # 最後の打牌・手番
        self.last_tsumo = None
        self.last_dahai = None
        self.last_teban = None

        # カンの個数
        self.n_kan = 0

        # プログラムカウンター
        self.pc = 0

        # 通知
        self.ronho_decisions = dict()
        self.minkan_decisions = dict()
        self.pon_decisions = dict()
        self.chi_decisions = dict()

        # 状態
        self.prev_state, self.state = self.state, GameBase.KYOKU_START_STATE

    def tsumoho(self, player):
        if player.can_tsumoho():
            self.tsumoho_decisions[player.position] = True
            self.ankan_decisions[player.position] = None
            self.richi_decisions[player.position] = False

    def ankan(self, pais, player):
        if player.can_ankan(pais):
            self.tsumoho_decisions[player.position] = False
            self.ankan_decisions[player.position] = pais
            self.richi_decisions[player.position] = False

    def richi_declare(self, player):
        for i in player.tehai:
            if player.can_richi_declare(i):
                self.tsumoho_decisions[player.position] = False
                self.ankan_decisions[player.position] = None
                self.richi_decisions[player.position] = True
                break

    def dahai(self, dahai, player):
        if player.can_dahai(dahai):
            self.dahai_decisions[player.position] = dahai

    def ronho(self, player):
        if player.can_ronho():
            self.ronho_decisions[player.position] = True
            self.pon_decisions[player.position] = [None, None]
            self.chi_decisions[player.position] = [None, None]

    def pon(self, pais, pai, player):
        if player.can_pon(pais, pai):
            self.ronho_decisions[player.position] = False
            self.pon_decisions[player.position] = [pais, pai]
            self.chi_decisions[player.position] = [None, None]

    def chi(self, pais, pai, player):
        if player.can_chi(pais, pai):
            self.ronho_decisions[player.position] = False
            self.pon_decisions[player.position] = [None, None]
            self.chi_decisions[player.position] = [pais, pai]

    def next_kyoku(self):
        if self.state == GameBase.AGARI_STATE:
            self.state = GameBase.KYOKU_START_STATE
        elif self.state == GameBase.RYUKYOKU_STATE:
            self.state = GameBase.KYOKU_START_STATE
