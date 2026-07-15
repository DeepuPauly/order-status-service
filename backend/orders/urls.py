from django.urls import path

from . import views

urlpatterns = [
    path("ingest/", views.ingest),
    path("orders/", views.order_list),
    path("orders/<str:order_id>/", views.order_detail),
]