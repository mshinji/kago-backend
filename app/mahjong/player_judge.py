from .agari import Agari
from .game_base import GameBase
from .shanten import calc_shanten


class PlayerJudge:
    def can_tsumoho(self):
        if self.game.teban != self.position:
            # print('手番じゃない')
            return False
        # TODO calc_chantenの方をこっちに合わせる
        tehai = [0] * 136
        for i in self.tehai:
            tehai[i] += 1
        if calc_shanten(tehai, len(self.huro)) >= 0:
            # print('和了ってない')
            return False
        # TODO パオ
        if Agari(self, self.game).score_movements == [0, 0, 0, 0]:
            # print('役無し')
            return False

        return True

    # TODO shanten.pyに組み込む
    def is_tenpai(self, dahai):
        tehai = [0] * 136
        for i in self.tehai:
            if i != dahai:
                tehai[i] += 1
        return bool(calc_shanten(tehai, len(self.huro)) <= 0)

    def can_dahai(self, dahai):
        if self.game.teban != self.position:
            # print('手番じゃない')
            return False
        if self.game.state not in [GameBase.NOTICE1_STATE, GameBase.DAHAI_STATE]:
            # print('ステート異常')
            return False
        if dahai not in self.tehai:
            # print('手牌に打牌する牌がない')
            return False
        if self.is_richi_complete and dahai != self.game.last_tsumo:
            # print('リーチ後にツモ切りしてない')
            return False
        richi = self.is_richi_declare and not self.is_richi_complete
        if richi and not self.is_tenpai(dahai):
            # print('聴牌しないリーチ宣言牌')
            return False

        return True

    def can_richi_declare(self, dahai):
        if self.game.teban != self.position:
            # print('手番じゃない')
            return False
        if self.is_richi_complete:
            # print('リーチしている')
            return False
        if self.game.state not in [GameBase.TSUMO_STATE, GameBase.NOTICE1_STATE, GameBase.DAHAI_STATE]:
            # print('ステート異常')
            return False
        huro_types = [huro['type'] for huro in self.huro]
        if len(huro_types) - huro_types.count('ankan') != 0:
            # print('門前じゃない')
            return False
        if self.game.scores[self.position] < 1000:
            # print('1000点ない')
            return False
        if not self.is_tenpai(dahai):
            # print('テンパってない')
            return False

        return True

    def can_ankan(self, ankan):
        if self.game.teban != self.position:
            # print('手番じゃない')
            return False
        if self.game.state != GameBase.TSUMO_STATE and self.game.state != GameBase.NOTICE1_STATE:
            # print('ステート以上')
            return False
        if self.game.n_kan >= 4:
            # print('カンの個数が4以上')
            return False
        if len(self.game.yama) <= 0:
            # print('山に牌が1つ以上')
            return False
        if len(ankan) != 4:
            # print('牌の数が4つじゃない')
            return False
        if len(set(ankan)) != 4:
            # print('牌番号に同じものがある')
            return False
        if len(set([i // 4 for i in ankan])) != 1:
            # print('牌を4で割った商が全て同じじゃない')
            return False
        for i in ankan:
            if i not in self.tehai:
                # print('手牌に含まれていない牌がある')
                return False
        return True

    def can_ronho(self):
        if self.game.teban == self.position:
            # print('捨てた本人')
            return False
        # TODO calc_chantenの方をこっちに合わせる
        tehai = [0] * 136
        for i in self.tehai + [self.game.last_dahai]:
            tehai[i] += 1
        if calc_shanten(tehai, len(self.huro)) >= 0:
            # print('和了ってない')
            return False
        # TODO パオ
        if Agari(self, self.game).score_movements == [0, 0, 0, 0]:
            # print('役無し')
            return False

        return True

    def can_pon(self, pais, pai):
        if self.game.teban == self.position:
            # print('捨てた本人')
            return False
        if self.is_richi_complete:
            # print('リーチしている')
            return False
        if self.game.state != GameBase.DAHAI_STATE and self.game.state != GameBase.NOTICE2_STATE:
            # print('ステート異常')
            return False
        if pai not in pais:
            # print('鳴いた牌が含まれていない')
            return False
        if self.game.last_dahai != pai:
            # print('鳴いた牌が最後の打牌と不一致')
            return False
        if len(pais) != 3:
            # print('牌の数が3つじゃない')
            return False
        for i in range(3):
            if pais[i] != pai and pais[i] not in self.tehai:
                # print('手牌に含まれていない牌がある')
                return False
        if not pais[0] // 4 == pais[1] // 4 == pais[2] // 4:
            # print('同じじゃない', pais, pai, self.tehai)
            return False
        if len(set(pais)) != 3:
            # print('牌番号に同じものがある')
            return False
        print('can_pon', pais)
        return True

    def can_chi(self, pais, pai):
        if (self.game.teban + 1) % 4 != self.position:
            # print('次の手番じゃない')
            return False
        if self.is_richi_complete:
            # print('リーチしている')
            return False
        if self.game.state != GameBase.DAHAI_STATE and self.game.state != GameBase.NOTICE2_STATE:
            # print('ステート異常')
            return False
        if pai not in pais:
            # print('鳴いた牌が含まれていない')
            return False
        if self.game.last_dahai != pai:
            # print('鳴いた牌が最後の打牌と不一致')
            return False
        if len(pais) != 3:
            # print('牌の数が3つじゃない')
            return False
        for i in range(3):
            if pais[i] != pai and pais[i] not in self.tehai:
                # print('手牌に含まれていない牌がある')
                return False
        pais.sort()
        if pais[2] // 4 - pais[1] // 4 != 1 or pais[1] // 4 - pais[0] // 4 != 1:
            # print('連続していない', pais, pai)
            return False
        if pais[0] >= 4 * 27:
            # print('字牌')
            return False
        if pais[0] // (4 * 9) != pais[2] // (4 * 9):
            # print('複数の種類の牌がある')
            return False
        if len(set(pais)) != 3:
            # print('牌番号に同じものがある')
            return False
        print('can_chi', pais)
        return True
