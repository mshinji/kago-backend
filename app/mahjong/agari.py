from itertools import combinations


class Agari:
    # 定数
    YAOCHU1 = [0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33]
    YAOCHU2 = [0, 6, 9, 15, 18, 24]
    YAKU = ['門前清自摸和', '立直', '一発', '槍槓', '嶺上開花',
            '海底摸月', '河底撈魚', '平和', '断幺九', '一盃口',
            '自風 東', '自風 南', '自風 西', '自風 北', '場風 東',
            '場風 南', '場風 西', '場風 北', '役牌 白', '役牌 發',
            '役牌 中', '両立直', '七対子', '混全帯幺九', '一気通貫',
            '三色同順', '三色同刻', '三槓子', '対々和', '三暗刻',
            '小三元', '混老頭', '二盃口', '純全帯幺九', '混一色',
            '清一色', '', '天和', '地和', '大三元',
            '四暗刻', '四暗刻単騎', '字一色', '緑一色', '清老頭',
            '九蓮宝燈', '純正九蓮宝燈', '国士無双', '国士無双１３面', '大四喜',
            '小四喜', '四槓子', 'ドラ', '裏ドラ', '赤ドラ']

    def __init__(self, player, game):
        self.player = player
        self.game = game

        self.tehai = [0] * 34
        for i in player.tehai:
            self.tehai[i // 4] += 1

        self.huro = []
        for h in player.huro:
            if h['type'] == 'chi':
                self.huro += [h['pais'][0] // 4, -1, -1]
            if h['type'] == 'pon':
                self.huro += [h['pais'][0] // 4, -1, -2]
            if h['type'] == 'minkan':
                self.huro += [h['pais'][0] // 4, -1, -8]
            if h['type'] == 'kakan':
                self.huro += [h['pais'][0] // 4, -1, -8]
            if h['type'] == 'ankan':
                self.huro += [h['pais'][0] // 4, -1, -16]

        if game.teban == player.position:
            self.machi = game.last_tsumo // 4
            self.ba = [game.kyoku, game.honba, game.kyotaku, player.position, player.position]
        else:
            self.tehai[game.last_dahai // 4] += 1
            self.machi = game.last_dahai // 4
            self.ba = [game.kyoku, game.honba, game.kyotaku, player.position, game.last_teban]

        self.zenpai = self.tehai[::]
        for i in range(0, len(self.huro), 3):
            if self.huro[i+2] <= -2:
                self.zenpai[self.huro[i]] += 3
            else:
                self.zenpai[self.huro[i]] += 1
                self.zenpai[self.huro[i]+1] += 1
                self.zenpai[self.huro[i]+2] += 1

        self.agaris = []

        self.menzen = 1 if len(self.huro) - self.huro.count(-16) * 3 == 0 else 0
        self.tsumo = 1 if self.ba[3] == self.ba[4] else 0

        # 状況役と全部役を定義
        self.jokyo_yaku = self.get_jokyo_yaku()
        self.zenbu_yaku = self.get_zenbu_yaku()
        self.bubun_yaku = [0] * 55

        # 一般手の和了形を全て抜き出す
        for i in range(34):
            if self.tehai[i] >= 2:
                self.tehai[i] -= 2
                self.get_mentsu([], i, 0)
                self.tehai[i] += 2

        self.get_ten()

        self.yaku = [0] * 55
        for i in range(55):
            self.yaku[i] += self.zenbu_yaku[i] + self.bubun_yaku[i] + self.jokyo_yaku[i]

    def get_ten(self):
        max = [0, 0]
        for agari in self.agaris:
            for i in range(len(self.huro), 13):
                if self.machi == agari[i]:
                    # 双ポンロンの場合明刻に変換
                    if not self.tsumo and i in range(0, 3*4, 3) and agari[i+2] == -4:
                        agari[i+2] = -2
                        hu = self.get_hu(agari, i)
                        bubun_yaku = self.get_bubun_yaku(agari)
                        agari[i+2] = -4
                    else:
                        hu = self.get_hu(agari, i)
                        bubun_yaku = self.get_bubun_yaku(agari)

                    # 平和
                    if hu == 20 and self.menzen:
                        bubun_yaku[7] = 1

                    han = sum(self.jokyo_yaku) + sum(self.zenbu_yaku) + sum(bubun_yaku)
                    if han == sum([self.jokyo_yaku[Agari.YAKU.index(yaku)] for yaku in ['ドラ', '裏ドラ', '赤ドラ']]):
                        hu = -float('inf')
                        han = -float('inf')

                    # ツモ符計算
                    # 喰い平和形
                    if hu == 20 and not self.menzen:
                        hu = 30
                    # 門前ロン
                    elif (not self.tsumo) and self.menzen:
                        hu += 10
                    # ツモ(平和除く)
                    elif hu != 20 and self.tsumo:
                        hu += 2

                    hu = -(-hu // 10) * 10

                    if hu * (2 ** han) > max[0] * (2 ** max[1]):
                        max = [hu, han]
                        self.bubun_yaku = bubun_yaku[::]

        # 七対子
        if self.tehai.count(2) == 7:
            han = sum(self.jokyo_yaku) + sum(self.zenbu_yaku) + 2
            if 25 * (2 ** han) > max[0] * (2 ** max[1]):
                max = [25, han]
                self.bubun_yaku = [2 if i == 22 else 0 for i in range(0, 55)]

        # 国士無双
        if sum([1 if self.tehai[i] >= 1 else -1 for i in Agari.YAOCHU1]) == 13:
            han = sum(self.jokyo_yaku[37:39]) + 13
            max = [1, han]
            self.bubun_yaku = [13 if i == 47 else 0 for i in range(0, 55)]

        if sum(self.jokyo_yaku[37:52] + self.zenbu_yaku[37:52] + self.bubun_yaku[37:52]) != 0:
            self.jokyo_yaku = [self.jokyo_yaku[i] if 37 <= i <= 51 else 0 for i in range(0, 55)]
            self.zenbu_yaku = [self.zenbu_yaku[i] if 37 <= i <= 51 else 0 for i in range(0, 55)]
            self.bubun_yaku = [self.bubun_yaku[i] if 37 <= i <= 51 else 0 for i in range(0, 55)]
            han = sum(self.jokyo_yaku + self.zenbu_yaku + self.bubun_yaku)

        # 点数変動計算
        score_movements = [0, 0, 0, 0]

        ten = max[0] * (2 ** (max[1] + 2))
        if ten >= 2000:
            if max[1] >= 13:
                ten = 8000 * (max[1] // 13)
            elif max[1] >= 11:
                ten = 6000
            elif max[1] >= 8:
                ten = 4000
            elif max[1] >= 6:
                ten = 3000
            else:
                ten = 2000

        if self.ba[3] == self.ba[0] % 4:
            ten *= 6
        else:
            ten *= 4

        ten = -(-ten // 100)

        if self.tsumo:
            # 包ツモ
            if len(self.ba) == 6:
                score_movements[self.ba[3]] = ten + self.ba[1] * 3 + self.ba[2] * 10
                score_movements[self.ba[5]] = -ten - self.ba[1] * 3

            # 親ツモ
            elif self.ba[3] == self.ba[0] % 4:
                for i in range(0, 4):
                    if i == self.ba[3]:
                        score_movements[i] = -(-ten // 3) * 3 + (self.ba[1] * 3) + (self.ba[2] * 10)
                    else:
                        score_movements[i] = -ten // 3 - self.ba[1]
            # 子ツモ
            else:
                for i in range(0, 4):
                    if i == self.ba[3]:
                        score_movements[i] += self.ba[2] * 10
                    elif i == self.ba[0] % 4:
                        score_movements[i] = -ten // 2 - self.ba[1]
                        score_movements[self.ba[3]] -= score_movements[i]
                    else:
                        score_movements[i] = -ten // 4 - self.ba[1]
                        score_movements[self.ba[3]] -= score_movements[i]

        else:
            # 包ロン(包者と放銃者が存在)
            if len(self.ba) == 6:
                score_movements[self.ba[3]] = ten + self.ba[1] * 3 + self.ba[2] * 10
                score_movements[self.ba[4]] = -ten // 2
                score_movements[self.ba[5]] = -ten // 2 - self.ba[1] * 3

            # ロン
            else:
                score_movements[self.ba[3]] = ten + self.ba[1] * 3 + self.ba[2] * 10
                score_movements[self.ba[4]] = -ten - self.ba[1] * 3

        self.score_movements = [i * 100 for i in score_movements]

    # 全面子抜き出し
    def get_mentsu(self, tehai, janto, start):
        if sum(self.tehai) == 0:
            self.agaris.append(self.huro + tehai + [janto, janto])
            return

        if sum(self.tehai[0:start]) != 0:
            return

        for i in range(start, 34):
            if self.tehai[i] == 0:
                continue

            # 順子抜き出し
            if i <= 26 and i % 9 <= 6 and self.tehai[i + 1] and self.tehai[i + 2]:
                self.tehai[i] -= 1
                self.tehai[i+1] -= 1
                self.tehai[i+2] -= 1
                self.get_mentsu(tehai + [i, i + 1, i + 2], janto, i)
                self.tehai[i] += 1
                self.tehai[i+1] += 1
                self.tehai[i+2] += 1

            # 刻子抜き出し
            if self.tehai[i] >= 3:
                self.tehai[i] -= 3
                self.get_mentsu(tehai + [i, -1, -4], janto, i)
                self.tehai[i] += 3

    # ツモ符を除く符計算を行う
    def get_hu(self, agari, i):
        # 基本符
        hu = 20

        # 面子による符
        for j in range(0, 3*4, 3):
            tmp_hu = 0

            if agari[j+2] <= -2:
                tmp_hu = agari[j+2] * -1

            if agari[j] in Agari.YAOCHU1:
                tmp_hu *= 2

            hu += tmp_hu

        # 雀頭による符
        # 自風牌
        if agari[12] == (self.ba[3] - self.ba[0]) % 4 + 27:
            hu += 2
        # 場風牌
        if agari[12] == self.ba[0] // 4 + 27:
            hu += 2
        # 三元牌
        if 31 <= agari[12] <= 33:
            hu += 2

        # 待ちによる符
        # 単騎待ち
        if i == 12:
            hu += 2
        # 嵌張待ち
        elif i % 3 == 1 and agari[i+1] > 0:
            hu += 2
        # 辺張待ち(123)
        elif i % 3 == 2 and agari[i-2] % 9 == 0 and agari[i] > 0:
            hu += 2
        # 辺張待ち(789)
        elif i % 3 == 0 and agari[i] % 9 == 6 and agari[i+2] > 0:
            hu += 2

        return hu

    def get_dora(self, pai):
        if pai // 4 in [8, 17, 26]:
            return pai // 4 - 8

        if pai // 4 == 30:
            return 27

        if pai // 4 == 33:
            return 31

        return pai // 4 + 1

    # 全部役
    def get_zenbu_yaku(self):
        zenbu_yaku = [0 for i in range(0, 55)]

        # 役満
        # 39:大三元
        if self.zenpai[31] + self.zenpai[32] + self.zenpai[33] == 9:
            zenbu_yaku[39] = 13

        # 42:字一色
        if sum(self.zenpai[27:34]) == 14:
            zenbu_yaku[42] = 13

        # 43:緑一色
        if sum([self.zenpai[i] for i in [19, 20, 21, 23, 25, 32]]) == 14:
            zenbu_yaku[43] = 13

        # 44:清老頭
        if sum([self.zenpai[i] for i in [0, 8, 9, 17, 18, 26]]) == 14:
            zenbu_yaku[44] = 13

        # 45:九蓮宝燈
        if self.huro == []:
            for i in [0, 9, 18]:
                if self.zenpai[i] >= 3 and self.zenpai[i+8] >= 3 and 0 not in self.zenpai[i+1:i+8]:
                    zenbu_yaku[45] = 13

        # 49:大四喜
        if self.zenpai[27] + self.zenpai[28] + self.zenpai[29] + self.zenpai[30] == 12:
            zenbu_yaku[49] = 13

        # 50:小四喜
        if self.zenpai[27] + self.zenpai[28] + self.zenpai[29] + self.zenpai[30] == 11:
            zenbu_yaku[50] = 13

        # 役満以外
        # 8:断么九
        if sum([self.zenpai[i] for i in Agari.YAOCHU1]) == 0:
            zenbu_yaku[8] = 1

        # 34:混一色, 35:清一色
        for i in [0, 9, 18]:
            if sum(self.zenpai[i:i+9]) == 14:
                zenbu_yaku[35] = 5 + self.menzen
            elif sum(self.zenpai[i:i+9] + self.zenpai[27:34]) == 14:
                zenbu_yaku[34] = 2 + self.menzen

        # 10-13:自風, 14-17:場風, 18-20:役牌
        if self.zenpai[27 + (self.ba[3] - self.ba[0]) % 4] == 3:
            zenbu_yaku[10 + (self.ba[3] - self.ba[0]) % 4] = 1

        if self.zenpai[27 + (self.ba[0] // 4)] == 3:
            zenbu_yaku[14 + (self.ba[0] // 4)] = 1

        if self.zenpai[31] == 3:
            zenbu_yaku[18] = 1
        if self.zenpai[32] == 3:
            zenbu_yaku[19] = 1
        if self.zenpai[33] == 3:
            zenbu_yaku[20] = 1

        # 30:小三元
        if self.zenpai[31] + self.zenpai[32] + self.zenpai[33] == 8:
            zenbu_yaku[30] = 2

        # 31:混老頭
        if sum([self.zenpai[i] for i in Agari.YAOCHU1]) == 14:
            zenbu_yaku[31] = 2

        return zenbu_yaku

    # 部分役
    def get_bubun_yaku(self, agari):
        bubun_yaku = [0 for i in range(0, 55)]

        # 役満
        # 40:四暗刻
        if agari.count(-4) + agari.count(-16) == 4:
            bubun_yaku[40] = 13

        # 51:四槓子
        if agari.count(-8) + agari.count(-16) == 4:
            bubun_yaku[51] = 13

        # 役満以外
        # 9:一盃口, 32:二盃口
        if self.menzen:
            if agari[0:3] == agari[3:6] and agari[6:9] == agari[9:12]:
                bubun_yaku[32] = 3
            elif agari[0:3] == agari[3:6] or agari[3:6] == agari[6:9] or agari[6:9] == agari[9:12]:
                bubun_yaku[9] = 1

        # 23:混全帯幺九, 33:純全帯幺九
        if self.zenbu_yaku[31] != 2:
            for i in range(0, 3*4, 3):
                if agari[i+2] <= -2 and agari[i] in Agari.YAOCHU1:
                    continue
                if agari[i+2] >= -1 and agari[i] in Agari.YAOCHU2:
                    continue
                break
            else:
                if agari[12] in Agari.YAOCHU1:
                    if sum(self.zenpai[27:]) == 0:
                        bubun_yaku[33] = 2 + self.menzen
                    else:
                        bubun_yaku[23] = 1 + self.menzen

        # 24:一気通貫
        for i in [0, 9, 18]:
            for j in [0, 3, 6]:
                for k in range(0, 3*4, 3):
                    if agari[k + 2] >= -1 and agari[k] == i + j:
                        break
                else:
                    break
            else:
                bubun_yaku[24] = 1 + self.menzen
                break

        # 25:三色同順
        for i in combinations([agari[i] for i in range(0, 3*4, 3) if agari[i+2] >= -1], 3):
            if i[0] % 9 == i[1] % 9 == i[2] % 9 and i[0] != i[1] and i[0] != i[2] and i[1] != i[2]:
                bubun_yaku[25] = 1 + self.menzen
                break

        # 26:三色同刻
        for i in combinations([agari[i] for i in range(0, 3*4, 3) if agari[i+2] <= -2 and agari[i] <= 26], 3):
            if i[0] % 9 == i[1] % 9 == i[2] % 9 and i[0] != i[1] and i[0] != i[2] and i[1] != i[2]:
                bubun_yaku[25] = 2
                break

        # 27:三槓子
        if agari.count(-8) + agari.count(-16) == 3:
            bubun_yaku[27] = 2

        # 28:対々和
        if sum([1 for i in range(2, 3*4, 3) if agari[i] <= -2]) == 4:
            bubun_yaku[28] = 2

        # 29:三暗刻
        if sum([1 for i in range(2, 3*4, 3) if agari[i] == -4 or agari[i] == -16]) == 3:
            bubun_yaku[29] = 2

        return bubun_yaku

    def get_jokyo_yaku(self):
        jokyo_yaku = [0] * 55
        zenpai = [0] * 34
        huro_types = []
        for pai in self.player.tehai:
            zenpai[pai // 4] += 1
        for huro in self.player.huro:
            for pai in huro['pais']:
                zenpai[pai // 4] += 1
            huro_types.append(huro['type'])

        # 門前自摸
        if len(huro_types) - huro_types.count('ankan') == 0 and self.game.teban == self.player.position:
            jokyo_yaku[Agari.YAKU.index('門前清自摸和')] += 1
        # 立直
        if self.player.is_richi_complete and not 0 <= self.player.richi_pc <= 3:
            jokyo_yaku[Agari.YAKU.index('立直')] += 1
        # 一発
        if self.player.is_richi_complete and self.game.pc - self.player.richi_pc <= 4:
            jokyo_yaku[Agari.YAKU.index('一発')] += 1
        # TODO 槍槓
        # TODO 嶺上開花
        # 海底摸月
        if self.game.teban == self.player.position and len(self.game.yama) == 0:
            jokyo_yaku[Agari.YAKU.index('海底摸月')] += 1
        # 河底撈魚
        if self.game.teban != self.player.position and len(self.game.yama) == 0:
            jokyo_yaku[Agari.YAKU.index('河底撈魚')] += 1
        # 両立直
        if self.player.is_richi_complete and 0 <= self.player.richi_pc <= 3:
            jokyo_yaku[Agari.YAKU.index('両立直')] += 2
        # 天和
        if self.game.pc == 0 and self.game.teban == self.player.position:
            jokyo_yaku[Agari.YAKU.index('天和')] += 13
        # 地和
        if 1 <= self.game.pc <= 3 and self.game.teban == self.player.position:
            jokyo_yaku[Agari.YAKU.index('地和')] += 13
        # ドラ/裏ドラ
        for i in range(self.game.n_dora):
            jokyo_yaku[Agari.YAKU.index('ドラ')] += zenpai[self.get_dora(self.game.dora[i])]
            jokyo_yaku[Agari.YAKU.index('裏ドラ')] += zenpai[self.get_dora(self.game.dora[i + 5])]
        # 赤ドラ
        for pai in [16, 52, 88]:
            jokyo_yaku[Agari.YAKU.index('赤ドラ')] += self.tehai.count(pai)

        return jokyo_yaku
