from itertools import combinations


class PlayerMessage:
    def my_start_game(self):
        pass

    def start_kyoku_message(self):
        self.actions.append({
            'type': 'start_kyoku_message',
            'body': self.game_info()
        })

    def tsumoho_message(self, tsumoho):
        tsumoho = tsumoho.copy()
        tsumoho['scores'] = [tsumoho['scores'][i] for i, _ in self.prange()]
        tsumoho['scoreMovements'] = [tsumoho['scoreMovements'][i] for i, _ in self.prange()]

        self.actions.append({
            'type': 'tsumoho_message',
            'body': tsumoho
        })

    def tsumo_message(self, pai):
        data = {
            'type': 'tsumo_message',
            'body': {
                    'who': (self.game.teban - self.position) % 4,
                    'rest': len(self.game.yama)
            }
        }

        if self.game.teban == self.position:
            data['body']['pai'] = pai
        else:
            data['body']['dummy'] = self.game.make_dummy(pai)

        self.actions.append(data)

    def dahai_message(self, pai):
        self.actions.append({
            'type': 'dahai_message',
            'body': {
                'pai': pai,
                'dummy': self.game.make_dummy(pai),
                'who': (self.game.teban - self.position) % 4
            }
        })

    def richi_complete_message(self):
        self.actions.append({
            'type': 'richi_complete_message',
            'body': {
                'scores': [self.game.scores[i % 4] for i, _ in self.prange()],
                'richis': [player.is_richi_complete for _, player in self.prange()]
            }
        })

    def richi_bend_message(self, pai):
        self.actions.append({
            'type': 'richi_bend_message',
            'body': {
                'pai': pai,
                'voice': bool(not self.game.players[self.game.teban].is_richi_complete)
            }
        })

    def ankan_message(self, pais):
        self.actions.append({
            'type': 'ankan_message',
            'body': {
                'pais': pais,
                'dummies': self.game.make_dummies(pais),
                'who': (self.game.teban - self.position) % 4,
                'fromWho': (self.game.teban - self.position) % 4
            }
        })

    def ronho_message(self, ronho):
        ronho = ronho.copy()
        ronho['scores'] = [ronho['scores'][i] for i, _ in self.prange()]
        ronho['scoreMovements'] = [ronho['scoreMovements'][i] for i, _ in self.prange()]

        self.actions.append({
            'type': 'ronho_message',
            'body': ronho
        })

    def pon_message(self, pais, pai):
        self.actions.append({
            'type': 'pon_message',
            'body': {
                'pai': pai,
                'pais': pais,
                'dummies': self.game.make_dummies(pais),
                'who': (self.game.teban - self.position) % 4,
                'fromWho': (self.game.last_teban - self.position) % 4
            }
        })

    def chi_message(self, pais, pai):
        self.actions.append({
            'type': 'chi_message',
            'body': {
                'pai': pai,
                'pais': pais,
                'dummies': self.game.make_dummies(pais),
                'who': (self.game.teban - self.position) % 4,
                'fromWho': (self.game.last_teban - self.position) % 4
            }
        })

    def open_dora_message(self):
        pai = self.game.dora[self.game.n_dora - 1]
        self.actions.append({
            'type': 'open_dora_message',
            'body': {
                'pai': pai,
                'dummy': self.game.make_dummy(pai),
                'rest': len(self.game.yama)
            }
        })

    # TODO テンパイではリーチ棒情報が出ない
    # TODO 時間がないのでとりあえず動作も同時に
    def ryukyoku_message(self):
        is_tenpais = []
        for player in self.game.players:
            is_tenpais.append(bool(player.calc_shanten() <= 0))

        n_tenpai = is_tenpais.count(True)
        scores = []
        score_movements = []
        for i, player in enumerate(self.game.players):
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

            self.game.scores[i] += score_movements[i]
            scores.append(self.game.scores[i])

        # 四回実行されちゃうので
        if self.position == 0:
            self.game.honba += 1
            if not is_tenpais[self.game.kyoku % 4]:
                self.game.kyoku += 1

        self.actions.append({
            'type': 'ryukyoku_message',
            'body': {
                'scores': [scores[i % 4] for i in range(self.position, self.position + 4)],
                'scoreMovements': [score_movements[i % 4] for i in range(self.position, self.position + 4)]
            }
        })

    # TODO トップの人にリーチ棒を
    def syukyoku_message(self):
        scores = [self.game.scores[i] for i in range(4)]
        order_scores = sorted(scores, reverse=True)
        ranks = [order_scores.index(scores[i]) + 1 for i in range(4)]

        self.actions.append({
            'type': 'syukyoku_message',
            'body': {
                'scores': [scores[i % 4] for i in range(self.position, self.position + 4)],
                'ranks': [ranks[i % 4] for i in range(self.position, self.position + 4)]
            }
        })

    # 通知1(ツモ和/リーチ/暗槓/加槓)
    def tsumoho_notice_message(self):
        if self.can_tsumoho():
            self.actions.append({'type': 'tsumoho_notice_message'})
        else:
            self.game.tsumoho_decisions[self.position] = False

    def richi_notice_message(self):
        for i in self.tehai:
            if self.can_richi_declare(i):
                self.actions.append({
                    'type': 'richi_notice_message',
                })
                break

    def richi_declare_notice_message(self):
        action = {
            'type': 'richi_declare_notice_message',
            'body': []
        }

        for i in self.tehai:
            if self.can_richi_declare(i):
                action['body'].append({
                    'pai': i,
                })

        if len(action['body']) != 0:
            self.actions.append(action)

    def ankan_notice_message(self):
        action = {
            'type': 'ankan_notice_message',
            'body': []
        }

        for i in range(34):
            if self.can_ankan([i * 4 + j for j in range(4)]):
                action['body'].append({
                    'pais': [i * 4 + j for j in range(4)],
                    'dummies': self.game.make_dummies([i * 4 + j for j in range(4)])
                })

        if len(action['body']) == 0:
            self.game.ankan_decisions[self.position] = None
        else:
            self.actions.append(action)

    # 通知2(ロン和/明槓/ポン/チー)
    def ronho_notice_message(self):
        if self.can_ronho():
            self.actions.append({'type': 'ronho_notice_message'})
        else:
            self.game.ronho_decisions[self.position] = False

    def pon_notice_message(self):
        action = {
            'type': 'pon_notice_message',
            'body': []
        }

        done = [[0] * 2 for _ in range(34)]
        aka = [16, 52, 88]
        for i, j in combinations(self.tehai, 2):
            if not i // 4 == j // 4 == self.game.last_dahai // 4:
                continue

            if i in aka or j in aka or self.game.last_dahai in aka:
                if done[i // 4][1] == 0:
                    pais = [self.game.last_dahai, i, j]
                    if self.can_pon(pais, self.game.last_dahai):
                        action['body'].append({
                            'pai': self.game.last_dahai,
                            'pais': pais,
                            'dummies': self.game.make_dummies(pais),
                            'fromWho': (self.game.last_teban - self.position) % 4
                        })
                        done[i // 4][1] = 1
            else:
                if done[i // 4][0] == 0:
                    pais = [self.game.last_dahai, i, j]
                    if self.can_pon(pais, self.game.last_dahai):
                        action['body'].append({
                            'pai': self.game.last_dahai,
                            'pais': pais,
                            'dummies': self.game.make_dummies(pais),
                            'fromWho': (self.game.last_teban - self.position) % 4
                        })
                        done[i // 4][0] = 1

        if len(action['body']) == 0:
            self.game.pon_decisions[self.position] = [None, None]
        else:
            self.actions.append(action)

    def chi_notice_message(self):
        action = {
            'type': 'chi_notice_message',
            'body': []
        }

        tmp = set(map(self.game.make_simple, self.tehai))
        tehai = []
        for i in self.tehai:
            if self.game.make_simple(i) in tmp:
                tehai.append(i)
                tmp.remove(self.game.make_simple(i))

        for i, j in combinations(tehai, 2):
            pais = [self.game.last_dahai, i, j]
            if self.can_chi(pais, self.game.last_dahai):
                action['body'].append({
                    'pai': self.game.last_dahai,
                    'pais': pais,
                    'dummies': self.game.make_dummies(pais),
                    'fromWho': (self.game.last_teban - self.position) % 4
                })

        if len(action['body']) == 0:
            self.game.chi_decisions[self.position] = [None, None]
        else:
            self.actions.append(action)
