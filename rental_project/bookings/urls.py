from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('my/', views.my_bookings, name='my_bookings'),
    path('owner/', views.owner_bookings, name='owner_bookings'),
    path('create/<int:item_id>/', views.create_booking, name='create_booking'),
    path('<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('confirm/<int:booking_id>/', views.confirm_booking, name='confirm_booking'),
    path('reject/<int:booking_id>/', views.reject_booking, name='reject_booking'),
    path('return/<int:booking_id>/', views.return_booking, name='return_booking'),
    path('report-damage/<int:booking_id>/', views.report_damage, name='report_damage'),
    path('dispute/<int:booking_id>/', views.dispute_detail, name='dispute_detail'),
    path('dispute/<int:booking_id>/accept/', views.dispute_accept, name='dispute_accept'),
    path('dispute/<int:booking_id>/contest/', views.dispute_contest, name='dispute_contest'),
    path('confirm-receipt/<int:booking_id>/', views.confirm_receipt, name='confirm_receipt'),
    path('confirm-return-no-damage/<int:booking_id>/', views.confirm_return_no_damage, name='confirm_return_no_damage'),
    path('confirm-payment/<int:booking_id>/', views.confirm_payment, name='confirm_payment'),
    path('confirm-refund/<int:booking_id>/', views.confirm_refund, name='confirm_refund'),
    path('refund-deposit/<int:booking_id>/', views.refund_deposit, name='refund_deposit'),
]