from django.contrib import admin
from django.urls import path
from santa_bot.views import show_start, allocation, del_allocation

urlpatterns = [
    path('admin/', admin.site.urls),
    path('<int:telegram_id>', show_start),
    path('game/<int:game_id>', allocation),
    path('delgame/<int:game_id>', del_allocation),
]
