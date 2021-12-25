class Const:
    # ゲームのモード
    NORMAL_MODE = 0
    VISIBLE_MODE = 1
    AUTO_MODE = 2

    # ステート
    INITIAL_STATE = 'INITIAL'
    KYOKU_START_STATE = 'KYOKUSTART'
    TSUMO_STATE = 'TSUMO'
    DAHAI_STATE = 'DAHAI'
    NOTICE1_STATE = 'NOTICE1'  # リーチ/暗槓/加槓
    NOTICE2_STATE = 'NOTICE2'  # ロン/明槓/ポン/チー
    NOTICE3_STATE = 'NOTICE3'  # 和了後や流局後の次局
    RYUKYOKU_STATE = 'RYUKYOKU'
    SYUKYOKU_STATE = 'SYUKYOKU'

    def __init__(self):
        pass
