from django.urls import path

from . import views

app_name = 'ratings'

urlpatterns = [
    path('rate/<int:reservation_pk>/', views.rate_view, name='rate'),
]