from django.urls import path

from . import views

app_name = "quiz"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/start/", views.api_start, name="api_start"),
    path("api/answer/", views.api_answer, name="api_answer"),
    path("api/next/", views.api_next, name="api_next"),
    path("api/status/", views.api_status, name="api_status"),
]
