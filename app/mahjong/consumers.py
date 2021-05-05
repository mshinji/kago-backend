import json

from channels.generic.websocket import AsyncWebsocketConsumer
from .game import Game


class MahjongConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        await self.close()

    async def send(self, data):
        data = json.dumps(data)
        print('send:', data)

        await super().send(text_data=data)

    async def receive(self, text_data):
        data = json.loads(text_data)
        data_type = data['type']
        print('receive:', data)

        if data_type == 'ready':
            await self.start_game(data['mode'])

        if data_type == 'tsumoho':
            self.game.tsumoho(self.player)
            await self.next()

        if data_type == 'dahai':
            self.game.dahai(data['body']['pai'], self.player)
            await self.next()

        if data_type == 'richi_declare':
            self.game.richi_declare(self.player)
            await self.next()

        if data_type == 'ankan':
            self.game.ankan(data['body']['pais'], self.player)
            await self.next()

        if data_type == 'ronho':
            self.game.ronho(self.player)
            await self.next()

        if data_type == 'pon':
            self.game.pon(data['body']['pais'], data['body']['pai'], self.player)
            await self.next()

        if data_type == 'chi':
            self.game.chi(data['body']['pais'], data['body']['pai'], self.player)
            await self.next()

        if data_type == 'next_kyoku':
            self.game.next_kyoku()
            await self.next()

        if data_type == 'cancel':
            self.player.cancel()
            await self.next()

        if data_type == 'next':
            await self.next()

    # start_gameだけはconsumerで
    async def start_game(self, mode):
        # GameにRoomに登録
        self.game = Game(mode)

        # ゲーム開始
        self.game.start_game()
        self.player = self.game.find_player(0)

        # データ送信
        data = [
            {
                'type': 'start_game',
                'body': {}
            }
        ]
        await self.send(data)

    async def next(self):
        while self.game.next():
            if len(self.player.actions) != 0:
                await self.send(self.player.actions)
                break
