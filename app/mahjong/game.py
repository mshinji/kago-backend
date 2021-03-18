from random import shuffle


class Game():
    NORMAL_MODE = 0
    VISIBLE_MODE = 1

    INITIAL_STATE = -100000000
    KYOKU_START_STATE = -10
    TSUMO_STATE = 0
    KAN_STATE = 1
    DAHAI_STATE = 4

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
        # self.yama = [i for i in range(136)]
        # shuffle(self.yama)
        # カンテスト用山生成
        self.yama = [i for i in range(4 * 4 * 4, 136)]
        shuffle(self.yama)
        x = [i for i in range(4 * 4 * 4)]
        self.yama = self.yama + x

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

        # 状態
        self.prev_state, self.state = self.state, Game.KYOKU_START_STATE

    def ankan(self, ankan, player):
        if player.can_ankan(ankan):
            player.ankan(ankan)
            kan_dora = self.open_kan_dora()
            for i, player in enumerate(self.players):
                if i == self.teban:
                    player.my_ankan(ankan)
                    player.all_open_kan_dora(kan_dora)
                else:
                    player.other_ankan(ankan)
                    player.all_open_kan_dora(kan_dora)

            self.prev_state = Game.KAN_STATE
            self.state = Game.TSUMO_STATE

    def dahai(self, dahai, player):
        if player.can_dahai(dahai):
            player.dahai(dahai)
            for i, player in enumerate(self.players):
                if i == self.teban:
                    player.my_dahai(dahai)
                else:
                    player.other_dahai(dahai)

            self.prev_state = self.DAHAI_STATE
            self.state = Game.TSUMO_STATE

    def routine(self):
        while True:
            if hasattr(self, 'state'):
                print('state:', self.state)

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

            # ツモ送信状態
            elif self.state == Game.TSUMO_STATE:
                if self.prev_state != Game.KAN_STATE:
                    self.teban = (self.teban + 1) % 4
                tsumo = self.players[self.teban].tsumo()

                # ツモ送信
                for i, player in enumerate(self.players):
                    if i == self.teban:
                        player.my_tsumo(tsumo)
                    else:
                        player.other_tsumo(tsumo)

                # カン通知送信
                self.players[self.teban].my_before_ankan()

                self.prev_state, self.state = self.state, Game.KAN_STATE
                yield True
                continue

            # カン受信状態(AIのみ)
            elif self.state == Game.KAN_STATE:
                # 人間なら受信を待つ
                if self.players[self.teban].type == 'human':
                    break

                # AIなら暗槓判断を取得
                if self.players[self.teban].type == 'kago':
                    ankan = self.players[self.teban].decide_ankan()
                    if ankan is None:
                        self.prev_state, self.state = self.state, Game.DAHAI_STATE
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

                    self.prev_state, self.state = self.state, Game.TSUMO_STATE
                    yield True
                    continue

            # 打牌受信状態(AIのみ)
            elif self.state == Game.DAHAI_STATE:
                # 人間なら受信を待つ
                if self.players[self.teban].type == 'human':
                    break

                # AIなら打牌判断を取得
                dahai = self.players[self.teban].decide_dahai()
                for i, player in enumerate(self.players):
                    if i == self.teban:
                        player.my_dahai(dahai)
                    else:
                        player.other_dahai(dahai)

                self.prev_state, self.state = self.state, Game.TSUMO_STATE
                yield True
                continue
