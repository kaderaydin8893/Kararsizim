from django.urls import path
from . import views

app_name = "polls"

urlpatterns = [
    path("", views.home, name="home"),
    path("anket/<int:pk>/", views.poll_detail, name="detail"),
]
