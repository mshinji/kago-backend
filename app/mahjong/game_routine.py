from .game_base import GameBase

# TODO ダブロン検証


class GameRoutine:
    def next(self):
        # 行動のリセット
        for player in self.players:
            player.reset_actions()

        # 局開始状態
        if self.state == GameBase.KYOKU_START_STATE:
            self.start_kyoku()
            for player in self.players:
                player.start_kyoku_message()

            self.prev_state, self.state = self.state, GameBase.TSUMO_STATE
            return True

        # ツモ状態
        elif self.state == GameBase.TSUMO_STATE:
            # ツモ
            if self.prev_state != GameBase.NOTICE1_STATE:
                self.teban = (self.teban + 1) % 4
            tsumo = self.yama.pop()
            self.players[self.teban].tsumo(tsumo)

            # 選択を格納
            self.ankan_decisions = dict()
            self.richi_decisions = dict()

            # 送信
            for player in self.players:
                player.tsumo_message(tsumo)
            self.players[self.teban].tsumoho_notice_message()
            self.players[self.teban].richi_notice_message()
            self.players[self.teban].ankan_notice_message()

            # AIの選択を格納
            player = self.players[self.teban]
            if player.type == 'kago':
                self.richi_decisions[player.position] = player.decide_richi()
                self.ankan_decisions[player.position] = player.decide_ankan()

            self.prev_state = GameBase.TSUMO_STATE
            self.state = GameBase.NOTICE1_STATE
            return True

        # 通知1受信状態
        elif self.state == GameBase.NOTICE1_STATE:
            if len(self.richi_decisions) != 1 or len(self.ankan_decisions) != 1:
                return False

            self.dahai_decisions = dict()

            # 暗槓の決定
            who, pais = list(self.ankan_decisions.items())[0]
            if pais is not None:
                self.players[who].ankan(pais)
                for player in self.players:
                    player.ankan_message(pais)

                self.prev_state = GameBase.NOTICE1_STATE
                self.state = GameBase.TSUMO_STATE
                return True

            # リーチの決定
            who, richi = list(self.richi_decisions.items())[0]
            if richi:
                self.players[who].richi_declare()
                for player in self.players:
                    player.richi_declare_notice_message()

                self.prev_state = GameBase.NOTICE1_STATE
                self.state = GameBase.DAHAI_STATE
                return True

            self.prev_state = GameBase.NOTICE1_STATE
            self.state = GameBase.DAHAI_STATE
            return True

        # 打牌受信状態
        elif self.state == GameBase.DAHAI_STATE:
            # AIの選択を格納
            player = self.players[self.teban]
            if player.position not in self.dahai_decisions and player.type == 'kago':
                self.dahai_decisions[player.position] = player.decide_dahai()

            if len(self.dahai_decisions) != 1:
                return False

            who, pai = list(self.dahai_decisions.items())[0]

            # 打牌
            self.players[who].dahai(pai)
            self.players[who].richi(pai)

            # 選択を格納
            self.ronho_decisions = dict()
            self.pon_decisions = dict()
            self.chi_decisions = dict()

            # 送信
            for player in self.players:
                player.dahai_message(pai)
                if pai in [player.richi_pai for player in self.players]:
                    player.richi_bend_message(pai)

                player.ronho_notice_message()
                player.pon_notice_message()
                player.chi_notice_message()

            # AIの選択を格納
            for player in self.players:
                if player.type == 'kago':
                    self.ronho_decisions[player.position] = False
                    self.pon_decisions[player.position] = [player.decide_pon(), self.last_dahai]
                    self.chi_decisions[player.position] = [player.decide_chi(), self.last_dahai]

            self.prev_state = GameBase.DAHAI_STATE
            self.state = GameBase.NOTICE2_STATE
            return True

        # 通知2受信状態
        elif self.state == GameBase.NOTICE2_STATE:
            if len(self.ronho_decisions) != 4 or len(self.pon_decisions) != 4 or len(self.chi_decisions) != 4:
                return False

            # ロン決定
            for who, tf in self.ronho_decisions.items():
                if not tf:
                    continue

                ronho = self.players[who].ronho()
                for player in self.players:
                    player.ronho_message(ronho)

            # ロンじゃなければリーチ成立
            for player in self.players:
                if player.is_richi_declare and not player.is_richi_complete:
                    player.richi_complete()
                    for player in self.players:
                        player.richi_complete_message()
                    break

            # ポン決定
            for who, (pais, pai) in self.pon_decisions.items():
                if pais is not None:
                    self.players[who].pon(pais, pai)
                    for player in self.players:
                        player.pon_message(pais, pai)

                    self.dahai_decisions = dict()
                    self.prev_state = GameBase.NOTICE2_STATE
                    self.state = GameBase.DAHAI_STATE
                    return True

            # チー決定
            for who, (pais, pai) in self.chi_decisions.items():
                if pais is not None:
                    self.players[who].chi(pais, pai)
                    for player in self.players:
                        player.chi_message(pais, pai)

                    self.dahai_decisions = dict()
                    self.prev_state = GameBase.NOTICE2_STATE
                    self.state = GameBase.DAHAI_STATE
                    return True

            self.prev_state = GameBase.NOTICE2_STATE
            self.state = GameBase.TSUMO_STATE
            return True
