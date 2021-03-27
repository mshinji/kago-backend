from random import shuffle

# TODO リーチ後のカンできるかどうか
# TODO 喰い替え禁止


class Game():
    NORMAL_MODE = 0
    VISIBLE_MODE = 1

    INITIAL_STATE = -100
    KYOKU_START_STATE = -10
    TSUMO_STATE = 0
    # NOTICE1 - リーチ/暗槓/加槓
    NOTICE1_STATE = 10
    DAHAI_STATE = 20
    # NOTICE2 - 明槓/ポン/チ
    NOTICE2_STATE = 30

    def __init__(self):
        self.mode = Game.NORMAL_MODE
        self.kyoku = 0
        self.honba = 0
        self.kyotaku = 0
        self.players = []
        self.scores = [25000, 25000, 25000, 25000]

    # 汎用関数
    def open_kan_dora(self):
        kan_dora = self.dora[self.n_dora]
        self.n_dora += 1
        return kan_dora

    def add_player(self, player):
        player.game = self
        self.players.append(player)

    def find_player(self, player_id):
        for player in self.players:
            if player.id == player_id:
                return player

    def set_mode(self, mode):
        self.mode = mode

    def make_dummy(self, original):
        if self.mode == Game.VISIBLE_MODE:
            return original
        return self.dummy[original]

    def make_dummies(self, original):
        if self.mode == Game.VISIBLE_MODE:
            return original
        return [self.dummy[o] for o in original]

    def make_simple(self, original):
        if original == 16:
            return 35
        if original == 52:
            return 36
        if original == 88:
            return 37
        return original // 4

    def prange(self):
        return [self.players[i % 4] for i in range(self.teban, self.teban + 4)]

    # アクション実行関数
    def start_game(self):
        shuffle(self.players)
        for i, player in enumerate(self.players):
            player.position = i

        self.state = Game.KYOKU_START_STATE
        self.prev_state = Game.INITIAL_STATE

    def start_kyoku(self):
        # 各プレイヤーの手牌・河・副露の初期化
        for player in self.players:
            player.tehai = []
            player.kawa = []
            player.huro = []
            player.richi_pc = None
            # 再現用
            player.richi_declaration_pai = None

        # リーチ初期化
        self.richis = [False, False, False, False]
        self.richi_declarations = [False, False, False, False]

        # 手番設定(最初は1引く)
        self.teban = (self.kyoku - 1) % 4

        # ダミーデータ生成
        self.dummy = [136 + i for i in range(136)]
        shuffle(self.dummy)

        # 山生成
        # self.yama = [i for i in range(136)]
        # shuffle(self.yama)

        # カン
        # original = [
        #     *list(range(0, 0 + 13)),
        #     *list(range(36, 36 + 13)),
        #     *list(range(72, 72 + 13)),
        #     *list(range(108, 108 + 13))
        # ]
        # チーしやすい
        original = [
            0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48,
            1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49,
            2, 6, 10, 14, 18, 22, 26, 30, 34, 38, 42, 46, 50,
            3, 7, 11, 15, 19, 23, 27, 31, 35, 39, 43, 47, 51
        ]
        # 上がりやすい
        # original = [
        #     0, 4, 8, 12, 16, 20, 21, 22, 24, 25, 124, 125, 126,
        #     36, 40, 44, 48, 52, 56, 57, 58, 60, 61, 128, 129, 130,
        #     72, 76, 80, 84, 88, 92, 93, 94, 96, 97, 132, 133, 134
        # ]
        self.yama = [i for i in range(136)]
        shuffle(self.yama)
        for i in original:
            self.yama.pop(self.yama.index(i))
        self.yama = self.yama[:len(self.yama)-14] + original + self.yama[len(self.yama)-14:]

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
        self.minkan_decisions = dict()
        self.pon_decisions = dict()
        self.chi_decisions = dict()

        # 状態
        self.prev_state, self.state = self.state, Game.KYOKU_START_STATE

    def tsumoho(self, player):
        if player.can_tsumoho():
            tsumoho = player.tsumoho()
            for player in self.players:
                player.tsumoho_message(tsumoho)

    def ankan(self, pais, player):
        if player.can_ankan(pais):
            self.ankan_decisions[player.position] = pais

    def dahai(self, dahai, richi, player):
        if player.can_dahai(dahai) and (not richi or player.can_richi(dahai)):
            self.ankan_decisions[player.position] = None
            self.dahai_decisions[player.position] = [dahai, richi]

    def pon(self, pais, pai, player):
        if player.can_pon(pais, pai):
            self.pon_decisions[player.position] = [pais, pai]
            self.chi_decisions[player.position] = [None, None]

    def chi(self, pais, pai, player):
        if player.can_chi(pais, pai):
            self.pon_decisions[player.position] = [None, None]
            self.chi_decisions[player.position] = [pais, pai]

    def next(self):
        # 行動のリセット
        for player in self.players:
            player.reset_actions()

        # 局開始状態
        if self.state == Game.KYOKU_START_STATE:
            self.start_kyoku()
            for player in self.players:
                player.start_kyoku_message()

            self.prev_state, self.state = self.state, Game.TSUMO_STATE
            return True

        # ツモ状態
        elif self.state == Game.TSUMO_STATE:
            # ツモ
            if self.prev_state != Game.NOTICE1_STATE:
                self.teban = (self.teban + 1) % 4
            tsumo = self.yama.pop()
            self.players[self.teban].tsumo(tsumo)

            # 選択を格納
            self.ankan_decisions = dict()
            self.dahai_decisions = dict()  # 人間用にここで宣言

            # 送信
            for player in self.players:
                player.tsumo_message(tsumo)
            self.players[self.teban].tsumoho_notice_message()
            self.players[self.teban].richi_notice_message()
            self.players[self.teban].ankan_notice_message()

            # AIの選択を格納
            player = self.players[self.teban]
            if player.type == 'kago':
                self.ankan_decisions[player.position] = player.decide_ankan()

            self.prev_state = Game.TSUMO_STATE
            self.state = Game.NOTICE1_STATE
            return True

        # 通知1受信状態
        elif self.state == Game.NOTICE1_STATE:
            if len(self.ankan_decisions) != 1:
                return False

            # 暗槓の決定
            who, pais = list(self.ankan_decisions.items())[0]
            if pais is not None:
                self.players[who].ankan(pais)
                for player in self.players:
                    player.ankan_message(pais)

                self.prev_state = Game.NOTICE1_STATE
                self.state = Game.TSUMO_STATE
                return True

            # AIの選択を格納
            player = self.players[self.teban]
            if player.type == 'kago':
                richi_decision = player.decide_richi()
                self.dahai_decisions[player.position] = [player.decide_dahai(richi_decision), richi_decision]

            self.prev_state = Game.NOTICE1_STATE
            self.state = Game.DAHAI_STATE
            return True

        # 打牌受信状態
        elif self.state == Game.DAHAI_STATE:
            if len(self.dahai_decisions) != 1:
                return False

            who, (pai, richi) = list(self.dahai_decisions.items())[0]

            # 打牌
            self.players[who].dahai(pai, richi)

            # 選択を格納
            self.pon_decisions = dict()
            self.chi_decisions = dict()

            # 送信
            for player in self.players:
                player.dahai_message(pai, richi)
                player.pon_notice_message()
                player.chi_notice_message()

            # AIの選択を格納
            for player in self.players:
                if player.type == 'kago':
                    self.pon_decisions[player.position] = [player.decide_pon(), self.last_dahai]
                    self.chi_decisions[player.position] = [player.decide_chi(), self.last_dahai]

            self.prev_state = Game.DAHAI_STATE
            self.state = Game.NOTICE2_STATE
            return True

        # 通知2受信状態
        elif self.state == Game.NOTICE2_STATE:
            if len(self.pon_decisions) != 4 or len(self.chi_decisions) != 4:
                return False

            # ロンじゃなければリーチ成立
            for i in range(4):
                if not self.richis[i] and self.richi_declarations[i]:
                    self.players[i].richi_complete()
                    for player in self.players:
                        player.richi_complete_message()
                    break

            # ポン決定
            for who, (pais, pai) in self.pon_decisions.items():
                if pais is not None:
                    self.players[who].pon(pais, pai)
                    for player in self.players:
                        player.pon_message(pais, pai)

                    self.prev_state = Game.NOTICE2_STATE
                    self.state = Game.DAHAI_STATE
                    self.dahai_decisions = dict()
                    return True

            # チー決定
            for who, (pais, pai) in self.chi_decisions.items():
                if pais is not None:
                    self.players[who].chi(pais, pai)
                    for player in self.players:
                        player.chi_message(pais, pai)

                    self.prev_state = Game.NOTICE2_STATE
                    self.state = Game.DAHAI_STATE
                    self.dahai_decisions = dict()
                    return True

            self.prev_state = Game.NOTICE2_STATE
            self.state = Game.TSUMO_STATE
            return True
