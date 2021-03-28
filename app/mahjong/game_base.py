class GameBase:
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
        self.mode = GameBase.NORMAL_MODE
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
        if self.mode == GameBase.VISIBLE_MODE:
            return original
        return self.dummy[original]

    def make_dummies(self, original):
        if self.mode == GameBase.VISIBLE_MODE:
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
