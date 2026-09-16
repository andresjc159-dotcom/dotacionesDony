from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.reporte, name="reporte"),
    path("prediccion/", views.prediccion, name="prediccion"),
    path("aplicar-minmax/", views.aplicar_minmax, name="aplicar_minmax"),
]
