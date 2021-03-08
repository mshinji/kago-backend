from random import shuffle


class Game():
    NORMAL_MODE = 0
    VISIBLE_MODE = 1

    TSUMO_STATE = 0
    BEFORE_RICHI_KAN_STATE = 1
    RICHI_KAN_STATE = 2
    BEFORE_DAHAI_STATE = 3
    DAHAI_STATE = 4

    def __init__(self):
        self.mode = Game.NORMAL_MODE
        self.kyoku = 0
        self.honba = 0
        self.kyotaku = 0
        self.players = []
        self.scores = [25000, 25000, 25000, 25000]
        self.richis = [False, False, False, False]

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

    def start_game(self):
        shuffle(self.players)
        for i, player in enumerate(self.players):
            player.position = i
            player.start_game()

    def start_kyoku(self):
        # プレイヤー関数のstart_kyoku呼び出し
        for player in self.players:
            player.start_kyoku()

        # 手番設定(最初は1引く)
        self.teban = (self.kyoku - 1) % 4

        # ダミーデータ生成
        self.dummy = [136 + i for i in range(136)]
        shuffle(self.dummy)

        # 山生成
        self.yama = [i for i in range(136)]
        shuffle(self.yama)

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
        for _ in range(13):
            for player in self.players:
                player.tsumo(self.yama.pop())

        # 最後の打牌
        self.last_dahai = -1

        # 状態
        self.state = Game.TSUMO_STATE

    # ルーチーン記述
    def next(self, dahai):
        # ツモ状態
        if self.state == Game.TSUMO_STATE:
            self.teban = (self.teban + 1) % 4
            tsumo = self.yama.pop()

            for i, player in enumerate(self.players):
                if i == self.teban:
                    player.tsumo(tsumo)
                    player.my_tsumo(tsumo)
                else:
                    player.other_tsumo(tsumo)

            # self.state = Game.BEFORE_RICHI_KAN_STATE
            self.state = Game.DAHAI_STATE

        # リーチ・カン送信状態
        elif self.state == Game.BEFORE_RICHI_KAN_STATE:
            for i, player in enumerate(self.players):
                if i == self.teban:
                    player.my_before_dahai()
                else:
                    player.other_before_dahai()

            self.state = Game.RICHI_KAN_STATE

        # リーチ・カン受信状態
        elif self.state == Game.RICHI_KAN_STATE:
            self.state = Game.BEFORE_DAHAI_STATE

        # 打牌受信状態
        elif self.state == Game.DAHAI_STATE:
            if self.players[self.teban].type == 'human' and dahai is None:
                self.skip()
                return

            # 人間なら引数, AIならメソッドで打牌を取得
            if self.players[self.teban].type == 'kago':
                dahai = self.players[self.teban].dahai()

            for i, player in enumerate(self.players):
                if i == self.teban:
                    player.my_dahai(dahai)
                else:
                    player.other_dahai(dahai)

            self.last_dahai = dahai
            self.state = Game.TSUMO_STATE

    def skip(self):
        for player in self.players:
            player.last_action = [{
                'type': 'skip'
            }]
