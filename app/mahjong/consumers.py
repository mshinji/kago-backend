import json
import random
import string
from time import sleep

from channels.generic.websocket import WebsocketConsumer

from mahjong.game import Game
from mahjong.human import Human
from mahjong.kago import Kago


class MahjongConsumer(WebsocketConsumer):
    rooms = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if MahjongConsumer.rooms is None:
            MahjongConsumer.rooms = {}

    def generate_token(self):
        randlst = [random.choice(string.ascii_letters + string.digits) for i in range(30)]
        return ''.join(randlst)

    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        self.close()

    def send(self, text_data):
        data = json.loads(text_data)
        print('send', data)
        super().send(text_data=text_data)

    def receive(self, text_data):
        data = json.loads(text_data)
        data_type = data['type']
        if 'token' in data and data['token'] in MahjongConsumer.rooms:
            self.game = MahjongConsumer.rooms.get(data.get('token'))
            self.player = self.game.find_player(0)

        print('receive:', data)
        # if hasattr(self, 'game') and hasattr(self.game, 'state'):
        #     print('state:', self.game.state)

        if data_type == 'ready':
            self.start_game(data['mode'])
            self.routine()

        elif data_type == 'ankan':
            self.game.ankan(data['body']['ankan'], self.player)
            self.send(text_data=json.dumps(self.player.actions))
            self.routine()

        elif data_type == 'dahai':
            self.game.dahai(data['body']['dahai'], self.player)
            self.send(text_data=json.dumps(self.player.actions))
            self.routine()

    # start_gameだけはconsumerで
    def start_game(self, mode):
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
        self.send(text_data=json.dumps(data))

    def routine(self):
        for r in self.game.routine():
            self.send(text_data=json.dumps(self.player.actions))
            sleep(0.2)
