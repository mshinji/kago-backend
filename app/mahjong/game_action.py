from random import shuffle

from .const import Const
from .kago import Kago
from .human import Human


class GameAction:
    def start_game(self, mode=Const.AUTO_MODE, player=None):
        self.mode = mode

        # Player関連
        self.players = []
        if mode == Const.AUTO_MODE:
            if player is not None:
                self.players.append(player)
            else:
                self.players.append(Kago(id=0, game=self))
            self.players.append(Kago(id=1, game=self))
            self.players.append(Kago(id=2, game=self))
            self.players.append(Kago(id=3, game=self))
        else:
            self.players.append(Human(id=0, game=self))
            self.players.append(Kago(id=1, game=self))
            self.players.append(Kago(id=2, game=self))
            self.players.append(Kago(id=3, game=self))

        # 半荘関連
        self.kyoku = 0
        self.honba = 0
        self.kyotaku = 0
        shuffle(self.players)
        for i, player in enumerate(self.players):
            player.position = i
            player.score = 25000

        self.prev_state = Const.INITIAL_STATE
        self.state = Const.KYOKU_START_STATE

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
        #     *list(range(0, 0 + 13)),
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
        # 四暗刻
        # original = [
        #     35, 0, 1, 2, 3,
        #     20, 21, 22, 36, 37, 38, 52, 53, 54, 68, 110, 70, 88,
        #     24, 25, 26, 40, 41, 42, 107, 57, 58, 72, 73, 74, 89,
        #     28, 101, 30, 44, 45, 46, 60, 61, 62, 76, 77, 78, 90,
        #     32, 33, 34, 48, 49, 50, 64, 65, 66, 80, 81, 82, 91
        # ]

        # self.yama = [i for i in range(136)]
        # shuffle(self.yama)
        # for i in original:
        #     self.yama.pop(self.yama.index(i))
        # self.yama = self.yama[:len(self.yama) - 14] + original + self.yama[len(self.yama) - 14:]

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
        self.prev_state = self.state
        self.state = Const.KYOKU_START_STATE

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

    def ryukyoku(self):
        is_tenpais = []
        for player in self.players:
            is_tenpais.append(bool(player.calc_shanten() <= 0))

        n_tenpai = is_tenpais.count(True)
        scores = []
        score_movements = []
        for i, player in enumerate(self.players):
            if is_tenpais[i] and n_tenpai == 1:
                score_movements.append(3000)
            if is_tenpais[i] and n_tenpai == 2:
                score_movements.append(1500)
            if is_tenpais[i] and n_tenpai == 3:
                score_movements.append(1000)
            if not is_tenpais[i] and n_tenpai == 1:
                score_movements.append(-1000)
            if not is_tenpais[i] and n_tenpai == 2:
                score_movements.append(-1500)
            if not is_tenpais[i] and n_tenpai == 3:
                score_movements.append(-3000)
            if n_tenpai == 0 or n_tenpai == 4:
                score_movements.append(0)

            player.score += score_movements[i]
            scores.append(player.score)

        self.honba += 1
        if not is_tenpais[self.kyoku % 4]:
            self.kyoku += 1

        return {
            'scores': scores,
            'scoreMovements': score_movements
        }

    def next_kyoku(self):
        if self.state == Const.AGARI_STATE:
            self.state = Const.KYOKU_START_STATE
        elif self.state == Const.RYUKYOKU_STATE:
            self.state = Const.KYOKU_START_STATE
