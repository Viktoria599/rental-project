from django.urls import path
from . import views

app_name = 'items'  # Добавьте эту строку

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('<int:item_id>/', views.item_detail, name='item_detail'),
    path('my-items/', views.my_items, name='my_items'),
    path('add/', views.add_item, name='add_item'),
    path('<int:item_id>/edit/', views.edit_item, name='edit_item'),
    path('<int:item_id>/delete/', views.delete_item, name='delete_item'),
    path('<int:item_id>/toggle-status/', views.toggle_status, name='toggle_status'),
    path('my-rented/', views.my_rented_items, name='my_rented_items'),
]