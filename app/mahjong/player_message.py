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

    def open_dora_message(self, pai):
        self.actions.append({
            'type': 'open_dora_message',
            'body': {
                'pai': pai,
                'dummy': self.game.make_dummy(pai),
                'rest': len(self.game.yama)
            }
        })

    # 通知1(ツモ和/リーチ/暗槓/加槓)
    def tsumoho_notice_message(self):
        if self.can_tsumoho():
            self.actions.append({'type': 'tsumoho_notice_message'})

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
                if done[i//4][1] == 0:
                    pais = [self.game.last_dahai, i, j]
                    if self.can_pon(pais, self.game.last_dahai):
                        action['body'].append({
                            'pai': self.game.last_dahai,
                            'pais': pais,
                            'dummies': self.game.make_dummies(pais),
                            'fromWho': (self.game.last_teban - self.position) % 4
                        })
                        done[i//4][1] = 1
            else:
                if done[i//4][0] == 0:
                    pais = [self.game.last_dahai, i, j]
                    if self.can_pon(pais, self.game.last_dahai):
                        action['body'].append({
                            'pai': self.game.last_dahai,
                            'pais': pais,
                            'dummies': self.game.make_dummies(pais),
                            'fromWho': (self.game.last_teban - self.position) % 4
                        })
                        done[i//4][0] = 1

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
