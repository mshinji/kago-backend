import json
import random
import string

from mahjong.game import Game
from mahjong.human import Human
from mahjong.kago import Kago
from channels.generic.websocket import AsyncWebsocketConsumer


class MahjongConsumer(AsyncWebsocketConsumer):
    rooms = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if MahjongConsumer.rooms is None:
            MahjongConsumer.rooms = {}

    def generate_token(self):
        randlst = [random.choice(string.ascii_letters + string.digits) for i in range(30)]
        return ''.join(randlst)

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        await self.close()

    async def receive(self, text_data):
        data = json.loads(text_data)
        data_type = data['type']
        if 'token' in data and data['token'] in MahjongConsumer.rooms:
            self.game = MahjongConsumer.rooms.get(data.get('token'))
            self.player = self.game.find_player(0)

        print('receive:', data)
        if hasattr(self, 'game') and hasattr(self.game, 'state'):
            print('state:', self.game.state)

        if data_type == 'ready':
            await self.start_game(data['mode'])

        elif data_type == 'start_game':
            await self.start_kyoku()

        elif data_type == 'start_kyoku':
            await self.next()

        elif data_type == 'next':
            await self.next()

        elif data_type == 'ankan' and self.game.teban == self.player.position \
                and self.game.state == Game.KAN_STATE:
            print('ANKANAKANAKKANKDSADJADKN')
            await self.next(ankan=data['body']['ankan'])

        elif data_type == 'dahai' and self.game.teban == self.player.position \
                and (self.game.state == Game.KAN_STATE or self.game.state == Game.DAHAI_STATE):
            await self.next(dahai=data['body']['dahai'], state=Game.DAHAI_STATE)

    def prange(self):
        return [i % 4 for i in range(self.player.position, self.player.position + 4)]

    def game_info(self):
        # 各種計算
        tehais = []
        for i in self.prange():
            if i == self.player.position:
                tehais.append(self.game.players[i].tehai)
            else:
                tehais.append(self.game.make_dummies(self.game.players[i].tehai))

        kawas = []
        for i in self.prange():
            if i == self.player.position:
                kawas.append(self.game.players[i].kawa)
            else:
                kawas.append(self.game.make_dummies(self.game.players[i].kawa))

        huros = []
        for i in self.prange():
            huros.append(self.game.players[self.player.position].huro)

        dora = self.game.dora[:self.game.n_dora] + self.game.make_dummies(self.game.dora[self.game.n_dora:5])

        scores = [self.game.scores[i] for i in self.prange()]
        richis = [self.game.richis[i] for i in self.prange()]
        kazes = ['東南西北'[(i - self.game.kyoku) % 4]for i in self.prange()]
        rest = len(self.game.yama)

        return {
            'tehais': tehais,
            'kawas': kawas,
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

    async def start_game(self, mode):
        # GameにRoomに登録
        self.game = Game()
        self.token = self.generate_token()
        MahjongConsumer.rooms[self.token] = self.game

        # GameにPlayerを登録
        self.game.add_player(Human(0))
        self.game.add_player(Kago(1))
        self.game.add_player(Kago(2))
        self.game.add_player(Kago(3))

        # GameにModeを設定
        self.game.set_mode(mode)

        # ゲーム開始
        self.game.start_game()
        self.player = self.game.find_player(0)

        # データ送信
        data = [
            {
                'type': 'start_game',
                'body': {
                    'token': self.token
                }
            }
        ]
        await self.send(text_data=json.dumps(data))

    async def start_kyoku(self):
        # 局開始
        self.game.start_kyoku()

        # データ送信
        data = [
            {
                'type': 'start_kyoku',
                'body': self.game_info()
            }
        ]
        await self.send(text_data=json.dumps(data))

    async def next(self, ankan=None, dahai=None, state=None):
        self.game.next(ankan=ankan, dahai=dahai, state=state)

        await self.send(text_data=json.dumps(self.player.actions))
