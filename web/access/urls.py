from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("island/<str:node_id>/", views.island_card, name="island_card"),
    path("route/", views.route, name="route"),
    path("ranked/", views.ranked, name="ranked"),
    path("connect/", views.connect, name="connect"),
    path("services/", views.services, name="services"),
    path("placement/", views.placement, name="placement"),
    path("data/", views.data_room, name="data"),
]
