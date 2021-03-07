from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/mahjong/', consumers.MahjongConsumer.as_asgi()),
]
