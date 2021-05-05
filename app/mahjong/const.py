class Const:
    # ゲームのモード
    NORMAL_MODE = 0
    VISIBLE_MODE = 1
    AUTO_MODE = 2

    # ステート
    INITIAL_STATE = -100
    KYOKU_START_STATE = -10
    TSUMO_STATE = 0
    # NOTICE1 - リーチ/暗槓/加槓
    NOTICE1_STATE = 10
    DAHAI_STATE = 20
    # NOTICE2 - 明槓/ポン/チ
    NOTICE2_STATE = 30
    AGARI_STATE = 40
    RYUKYOKU_STATE = 50
    SYUKYOKU_STATE = 60

    def __init__(self):
        pass
