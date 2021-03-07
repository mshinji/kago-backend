from django.shortcuts import render

# Create your views here.


def mahjong(request):
    return render(request, 'mahjong/mahjong.html')
