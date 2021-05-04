from .agari import Agari

# TODO decisionsはGameじゃなくてPlayerに持たせたほうが良い


class PlayerAction:
    def tsumoho(self):
        agari = Agari(self, self.game)
        yakus = []
        for i in range(len(Agari.YAKU)):
            if agari.yaku[i] > 0:
                yakus.append({'name': Agari.YAKU[i], 'han': agari.yaku[i]})

        doras = []
        uradoras = []
        for i in range(5):
            if i < self.game.n_dora:
                doras.append(self.game.dora[i])
                uradoras.append(self.game.dora[i + 5])
            else:
                doras.append(self.game.make_dummy(self.game.dora[i]))
                uradoras.append(self.game.make_dummy(self.game.dora[i + 5]))

        score_movements = agari.score_movements
        for i, score_movement in enumerate(score_movements):
            self.game.scores[i] += score_movement

        self.game.kyotaku = 0
        if self.position == self.game.kyoku % 4:
            self.game.honba += 1
        else:
            self.game.honba = 0
        if self.position != self.game.kyoku % 4:
            self.game.kyoku += 1

        return {
            'yakus': yakus,
            'doras': doras,
            'uradoras': uradoras,
            'scores': self.game.scores,
            'scoreMovements': score_movements,
        }

    def tsumo(self, pai):
        self.tehai.append(pai)
        self.tehai.sort()
        self.game.last_tsumo = pai

    def ankan(self, pais):
        for i in pais:
            self.tehai.pop(self.tehai.index(i))
        self.huro.append({'type': 'ankan', 'pais': pais})
        self.game.n_kan += 1
        self.game.pc += 10

    def richi_declare(self):
        self.is_richi_declare = True
        self.richi_pc = self.game.pc

    def dahai(self, pai):
        self.tehai.pop(self.tehai.index(pai))
        self.kawa.append(pai)
        self.game.last_dahai = pai
        self.game.last_teban = self.game.teban
        self.game.pc += 1

    def richi_complete(self):
        self.game.scores[self.position] -= 1000
        self.is_richi_complete = True
        self.game.kyotaku += 1

    def richi(self, pai):
        if self.is_richi_declare and self.richi_pai not in self.kawa:
            self.richi_pai = pai

    def ronho(self):
        agari = Agari(self, self.game)
        yakus = []
        for i in range(len(Agari.YAKU)):
            if agari.yaku[i] > 0:
                yakus.append({'name': Agari.YAKU[i], 'han': agari.yaku[i]})

        doras = []
        uradoras = []
        for i in range(5):
            if i < self.game.n_dora:
                doras.append(self.game.dora[i])
                if self.is_richi_complete:
                    uradoras.append(self.game.dora[i + 5])
                else:
                    uradoras.append(self.game.make_dummy(self.game.dora[i + 5]))

            else:
                doras.append(self.game.make_dummy(self.game.dora[i]))
                uradoras.append(self.game.make_dummy(self.game.dora[i + 5]))

        score_movements = agari.score_movements
        for i, score_movement in enumerate(score_movements):
            self.game.scores[i] += score_movement

        self.game.kyotaku = 0
        if self.position == self.game.kyoku % 4:
            self.game.honba += 1
        else:
            self.game.honba = 0
        if self.position != self.game.kyoku % 4:
            self.game.kyoku += 1

        return {
            'yakus': yakus,
            'doras': doras,
            'uradoras': uradoras,
            'scores': self.game.scores,
            'scoreMovements': score_movements,
        }

    def pon(self, pais, pai):
        for i in pais:
            if i != pai:
                self.tehai.pop(self.tehai.index(i))
        self.huro.append({'type': 'pon', 'pais': pais})
        self.game.players[self.game.last_teban].kawa.pop(
            self.game.players[self.game.last_teban].kawa.index(pai)
        )
        self.game.teban = self.position
        self.game.pc += 10

    def chi(self, pais, pai):
        for i in pais:
            if i != pai:
                self.tehai.pop(self.tehai.index(i))
        self.huro.append({'type': 'chi', 'pais': pais})
        self.game.players[self.game.last_teban].kawa.pop(
            self.game.players[self.game.last_teban].kawa.index(pai)
        )
        self.game.teban = self.position
        self.game.pc += 10

    def cancel(self):
        if self.game.teban == self.position:
            self.game.ankan_decisions[self.position] = None
            self.game.richi_decisions[self.position] = False

        self.game.ronho_decisions[self.position] = False
        self.game.minkan_decisions[self.position] = [None, None]
        self.game.pon_decisions[self.position] = [None, None]
        self.game.chi_decisions[self.position] = [None, None]

    def reset_actions(self):
        self.actions = []

    def game_info(self):
        tehais = []
        for i, player in self.prange():
            if i == self.position:
                tehais.append(player.tehai)
            else:
                tehais.append(self.game.make_dummies(player.tehai))

        kawas = []
        for i, player in self.prange():
            if i == self.position:
                kawas.append(player.kawa)
            else:
                kawas.append(self.game.make_dummies(player.kawa))

        richi_pais = []
        for player in self.game.players:
            if player.richi_pai is not None:
                richi_pais.append(player.richi_pai)

        huros = []
        for _, player in self.prange():
            huros.append(player.huro)

        dora = self.game.dora[:self.game.n_dora] + self.game.make_dummies(self.game.dora[self.game.n_dora:5])

        scores = [self.game.scores[i] for i, _ in self.prange()]
        richis = [player.is_richi_complete for _, player in self.prange()]
        kazes = ['東南西北'[(i - self.game.kyoku) % 4] for i, _ in self.prange()]
        rest = len(self.game.yama)

        return {
            'tehais': tehais,
            'kawas': kawas,
            'richiPais': richi_pais,
            'huros': huros,
            'kyoku': self.game.kyoku,
            'honba': self.game.honba,
            'kyotaku': self.game.kyotaku,
            'dora': dora,
            'rest': rest,
            'scores': scores,
            'richis': richis,
            'kazes': kazes,
        }
