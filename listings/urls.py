from django.urls import path

from . import views

app_name = 'listings'

urlpatterns = [
    path('', views.asset_list_view, name='asset_list'),
    path('new/', views.asset_create_view, name='asset_create'),
    path('<int:pk>/', views.asset_detail_view, name='asset_detail'),
    path('<int:pk>/edit/', views.asset_edit_view, name='asset_edit'),
    path('<int:pk>/delete/', views.asset_delete_view, name='asset_delete'),
]