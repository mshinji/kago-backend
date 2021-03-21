from random import shuffle


class Game():
    NORMAL_MODE = 0
    VISIBLE_MODE = 1

    INITIAL_STATE = -100
    KYOKU_START_STATE = -10
    TSUMO_STATE = 0
    # NOTICE1 - リーチ/暗槓/加槓
    NOTICE1_SEND_STATE = 5
    NOTICE1_RECIEVE_STATE = 10
    DAHAI_STATE = 20
    # NOTICE2 - 明槓/ポン/チー
    NOTICE2_SEND_STATE = 25
    NOTICE2_RECIEVE_STATE = 30

    def __init__(self):
        self.mode = Game.NORMAL_MODE
        self.kyoku = 0
        self.honba = 0
        self.kyotaku = 0
        self.players = []
        self.scores = [25000, 25000, 25000, 25000]
        self.richis = [False, False, False, False]

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

        # 手番設定(最初は1引く)
        self.teban = (self.kyoku - 1) % 4

        # ダミーデータ生成
        self.dummy = [136 + i for i in range(136)]
        shuffle(self.dummy)

        # 山生成
        self.yama = [i for i in range(136)]
        shuffle(self.yama)
        # カンテスト用山生成
        # self.yama = [i for i in range(4 * 4 * 4, 136)]
        # shuffle(self.yama)
        # x = [i for i in range(4 * 4 * 4)]
        # self.yama = self.yama + x

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
                player.tsumo()

        # 最後の打牌
        self.last_dahai = -1

        # カンの個数
        self.n_kan = 0

        # 通知
        self.minkan_dicisions = dict()
        self.pon_dicisions = dict()
        self.chi_dicisions = dict()

        # 状態
        self.prev_state, self.state = self.state, Game.KYOKU_START_STATE

    def ankan(self, ankan, player):
        if player.can_ankan(ankan):
            player.ankan(ankan)
            kan_dora = self.open_kan_dora()

            # 暗槓と槓ドラの送信
            for i, player in enumerate(self.players):
                if i == self.teban:
                    player.my_ankan(ankan)
                    player.all_open_kan_dora(kan_dora)
                else:
                    player.other_ankan(ankan)
                    player.all_open_kan_dora(kan_dora)

            self.prev_state = Game.NOTICE1_RECIEVE_STATE
            self.state = Game.TSUMO_STATE

    def chi(self, pais, pai, player):
        if player.can_chi(pais, pai):
            self.chi_dicisions[player.position] = [pais, pai]

    def dahai(self, dahai, player):
        if player.can_dahai(dahai):
            player.dahai(dahai)

            # 打牌の送信
            for i, player in enumerate(self.players):
                if i == self.teban:
                    player.my_dahai(dahai)
                else:
                    player.other_dahai(dahai)

            self.prev_state = self.DAHAI_STATE
            self.state = Game.NOTICE2_SEND_STATE

    def routine(self):
        while True:
            # if hasattr(self, 'state'):
            #   print('state:', self.state)

            # 行動のリセット
            for player in self.players:
                player.reset_actions()

            # 局開始状態
            if self.state == Game.KYOKU_START_STATE:
                self.start_kyoku()
                for i, player in enumerate(self.prange()):
                    player.my_start_kyoku()

                self.prev_state, self.state = self.state, Game.TSUMO_STATE
                yield True
                continue

            # ツモ状態
            elif self.state == Game.TSUMO_STATE:
                if self.prev_state != Game.NOTICE1_RECIEVE_STATE:
                    self.teban = (self.teban + 1) % 4
                tsumo = self.players[self.teban].tsumo()

                # ツモ送信
                for i, player in enumerate(self.players):
                    if i == self.teban:
                        player.my_tsumo(tsumo)
                    else:
                        player.other_tsumo(tsumo)

                self.prev_state, self.state = self.state, Game.NOTICE1_SEND_STATE
                yield True
                continue

            # 通知1(リーチ/暗槓/加槓)送信状態
            elif self.state == Game.NOTICE1_SEND_STATE:
                # 暗槓通知送信
                self.players[self.teban].my_ankan_notice()

                self.prev_state = Game.NOTICE1_SEND_STATE
                self.state = Game.NOTICE1_RECIEVE_STATE
                yield True
                continue

            # 通知1受信状態(AIのみ)
            elif self.state == Game.NOTICE1_RECIEVE_STATE:
                # 人間なら受信を待つ
                if self.players[self.teban].type == 'human':
                    break

                # AIなら暗槓判断を取得
                if self.players[self.teban].type == 'kago':
                    ankan = self.players[self.teban].decide_ankan()
                    if ankan is None:
                        self.prev_state = Game.NOTICE1_RECIEVE_STATE
                        self.state = Game.DAHAI_STATE
                        yield True
                        continue

                # 暗槓がある場合
                if ankan != []:
                    self.players[self.teban].ankan(ankan)
                    kan_dora = self.open_kan_dora()
                    for i, player in enumerate(self.players):
                        if i == self.teban:
                            player.my_ankan(ankan)
                            player.all_open_kan_dora(kan_dora)
                        else:
                            player.other_ankan(ankan)
                            player.all_open_kan_dora(kan_dora)

                    self.prev_state = Game.NOTICE1_RECIEVE_STATE
                    self.state = Game.TSUMO_STATE
                    yield True
                    continue

            # 打牌受信状態(AIのみ)
            elif self.state == Game.DAHAI_STATE:
                # 人間なら受信を待つ
                if self.players[self.teban].type == 'human':
                    break

                # AIなら打牌判断を取得
                dahai = self.players[self.teban].decide_dahai()
                self.players[self.teban].dahai(dahai)

                # 打牌の送信
                for i, player in enumerate(self.players):
                    if i == self.teban:
                        player.my_dahai(dahai)
                    else:
                        player.other_dahai(dahai)

                self.prev_state = Game.DAHAI_STATE
                self.state = Game.NOTICE2_SEND_STATE
                yield True
                continue

            # 通知2(明槓/ポン/チー)送信状態
            elif self.state == Game.NOTICE2_SEND_STATE:
                # 選択を格納
                self.pon_dicisions = dict()
                self.chi_dicisions = dict()

                # チー通知送信
                for player in self.prange():
                    # player.my_pon_notice()
                    player.my_chi_notice()

                # AIの選択を格納
                for player in self.prange():
                    if player.type == 'kago' and player.position not in self.chi_dicisions:
                        self.chi_dicisions[player.position] = [player.decide_chi(), self.last_dahai]

                self.prev_state = Game.NOTICE2_SEND_STATE
                self.state = Game.NOTICE2_RECIEVE_STATE
                yield True
                continue

            # 通知2受信状態
            elif self.state == Game.NOTICE2_RECIEVE_STATE:
                if len(self.chi_dicisions) != 4:
                    break

                flag = False

                # チー決定
                for who, (pais, pai) in self.chi_dicisions.items():
                    if pais is not None:
                        flag = True
                        self.players[who].chi(pais, pai)
                        for i, player in enumerate(self.players):
                            if i == self.teban:
                                player.my_chi(pais, pai)
                            else:
                                player.other_chi(pais, pai)
                        break

                if flag:
                    self.prev_state = Game.NOTICE2_RECIEVE_STATE
                    self.state = Game.DAHAI_STATE
                    yield True
                    continue

                self.prev_state = Game.NOTICE2_RECIEVE_STATE
                self.state = Game.TSUMO_STATE
                yield True
                continue
