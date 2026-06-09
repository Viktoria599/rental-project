from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('read/<int:notif_id>/', views.mark_as_read, name='mark_as_read'),
]