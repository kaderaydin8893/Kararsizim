from django.urls import path
from . import views

app_name = "polls"

urlpatterns = [
    path("", views.home, name="home"),
    path("anket/yeni/", views.create_poll, name="create"),
    path("anket/<int:pk>/", views.poll_detail, name="detail"),
    path("anket/<int:pk>/oy/", views.vote_poll, name="vote"),
    path("kullanici/<str:username>/", views.user_polls, name="user_polls"),
]
