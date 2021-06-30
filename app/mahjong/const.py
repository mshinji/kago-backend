class Const:
    # ゲームのモード
    NORMAL_MODE = 0
    VISIBLE_MODE = 1
    AUTO_MODE = 2

    # ステート
    INITIAL_STATE = 'INITIAL'
    KYOKU_START_STATE = 'KYOKUSTART'
    TSUMO_STATE = 'TSUMO'
    # NOTICE1 - リーチ/暗槓/加槓
    NOTICE1_STATE = 'NOTICE1'
    DAHAI_STATE = 'DAHAI'
    # NOTICE2 - 明槓/ポン/チ
    NOTICE2_STATE = 'NOTICE2'
    AGARI_STATE = 'AGARI'
    RYUKYOKU_STATE = 'RYUKYOKU'
    SYUKYOKU_STATE = 'SYUKYOKU'

    def __init__(self):
        pass
