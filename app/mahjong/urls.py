from django.urls import path

from . import views

urlpatterns = [
    path('', views.mahjong, name='mahjong'),
]
