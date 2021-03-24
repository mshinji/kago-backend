import json
import random
import string

from channels.generic.websocket import AsyncWebsocketConsumer
from mahjong.game import Game
from mahjong.human import Human
from mahjong.kago import Kago


class MahjongConsumer(AsyncWebsocketConsumer):
    rooms = None

    async def generate_token(self):
        randlst = [random.choice(string.ascii_letters + string.digits) for i in range(30)]
        return ''.join(randlst)

    async def connect(self):
        if MahjongConsumer.rooms is None:
            MahjongConsumer.rooms = {}
        await self.accept()

    async def disconnect(self, close_code):
        await self.close()

    async def send(self, data):
        data = json.dumps(data)
        print('send', data)
        await super().send(text_data=data)

    async def receive(self, text_data):
        data = json.loads(text_data)
        data_type = data['type']
        print('receive:', data)

        if 'token' in data and data['token'] in MahjongConsumer.rooms:
            self.game = MahjongConsumer.rooms.get(data.get('token'))
            self.player = self.game.find_player(0)

        if data_type == 'ready':
            await self.start_game(data['mode'])

        if data_type == 'tsumoho':
            self.game.tsumoho(self.player)
            await self.send(self.player.actions)

        if data_type == 'ankan':
            self.game.ankan(data['body']['pais'], self.player)
            await self.send(self.player.actions)

        if data_type == 'pon':
            self.game.pon(data['body']['pais'], data['body']['pai'], self.player)
            await self.next()

        if data_type == 'chi':
            self.game.chi(data['body']['pais'], data['body']['pai'], self.player)
            await self.next()

        if data_type == 'cancel':
            self.player.cancel()
            await self.next()

        if data_type == 'dahai':
            self.game.dahai(data['body']['pai'], data['body']['richi'], self.player)
            await self.send(self.player.actions)

        if data_type == 'next':
            await self.next()

    # start_gameだけはconsumerで
    async def start_game(self, mode):
        # GameにRoomに登録
        self.game = Game()
        self.token = await self.generate_token()
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
        await self.send(data)

    async def next(self):
        while self.game.next():
            if len(self.player.actions) != 0:
                await self.send(self.player.actions)
                break
