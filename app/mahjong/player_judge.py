from .agari import Agari
from .const import Const


class PlayerJudge:
    def can_tsumoho(self):
        if self.game.teban != self.position:
            # print('手番じゃない')
            return False
        if self.calc_shanten() >= 0:
            # print('和了ってない')
            return False
        # TODO パオ
        if Agari(self, self.game).score_movements == [0, 0, 0, 0]:
            # print('役無し')
            return False

        return True

    def can_dahai(self, dahai):
        if self.game.teban != self.position:
            # print('手番じゃない')
            return False
        if self.game.state not in [Const.NOTICE1_STATE, Const.DAHAI_STATE]:
            # print('ステート異常')
            return False
        if dahai not in self.tehai:
            # print('手牌に打牌する牌がない')
            return False
        if self.is_richi_complete and dahai != self.game.last_tsumo:
            # print('リーチ後にツモ切りしてない')
            return False
        if self.is_richi_declare and not self.is_richi_complete and self.calc_shanten(remove=[dahai]) > 0:
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
        if self.game.state not in [Const.TSUMO_STATE, Const.NOTICE1_STATE, Const.DAHAI_STATE]:
            # print('ステート異常')
            return False
        huro_types = [huro['type'] for huro in self.huro]
        if len(huro_types) - huro_types.count('ankan') != 0:
            # print('門前じゃない')
            return False
        if self.game.scores[self.position] < 1000:
            # print('1000点ない')
            return False
        if self.calc_shanten(remove=[dahai]) > 0:
            # print('テンパってない')
            return False

        return True

    def can_ankan(self, ankan):
        if self.game.teban != self.position:
            # print('手番じゃない')
            return False
        if self.game.state != Const.TSUMO_STATE and self.game.state != Const.NOTICE1_STATE:
            # print('ステート以上')
            return False
        if self.game.n_kan >= 4:
            # print('カンの個数が4以上')
            return False
        if len(self.game.yama) <= 0:
            # print('山に牌がない')
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
        if self.is_richi_complete:
            shanten1 = self.calc_shanten(remove=[self.game.last_tsumo])
            shanten2 = self.calc_shanten(remove=ankan)
            machi1 = self.get_yuko(remove=[self.game.last_tsumo])
            machi2 = self.get_yuko(remove=ankan)
            if shanten1 != shanten2 or machi1 != machi2:
                print('リーチ後に待ちの変わる暗槓')
                return False

        return True

    def can_ronho(self):
        if self.game.teban == self.position:
            # print('捨てた本人')
            return False
        if self.calc_shanten(add=[self.game.last_dahai]) >= 0:
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
        if self.game.state != Const.DAHAI_STATE and self.game.state != Const.NOTICE2_STATE:
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
        if self.game.state != Const.DAHAI_STATE and self.game.state != Const.NOTICE2_STATE:
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
