from django.urls import path

from . import views

app_name = 'transactions'

urlpatterns = [
    path('request/<int:asset_pk>/', views.reservation_request_view, name='reservation_request'),
    path('my-reservations/', views.my_reservations_view, name='my_reservations'),
    path('respond/<int:pk>/<str:action>/', views.reservation_respond_view, name='reservation_respond'),
    path('qr/<int:pk>/', views.reservation_qr_view, name='reservation_qr'),
    path('confirm/<uuid:token>/', views.reservation_confirm_view, name='reservation_confirm'),
    path('return-qr/<int:pk>/', views.return_qr_view, name='return_qr'),
    path('return-confirm/<uuid:token>/', views.return_confirm_view, name='return_confirm'),
]