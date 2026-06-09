from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import models
from django.contrib import messages
from bookings.models import Booking
from .models import Message
from notifications.models import Notification


@login_required
def chat_list(request):
    bookings = Booking.objects.filter(
        models.Q(renter=request.user) | models.Q(item__owner=request.user)
    ).distinct()
    return render(request, 'chat_list.html', {'bookings': bookings})


@login_required
def chat_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.user != booking.renter and request.user != booking.item.owner:
        return redirect('chat_list')
    
    if request.method == 'POST':
        text = request.POST.get('message')
        if text:
            # Создаём сообщение
            message = Message.objects.create(
                booking=booking,
                sender=request.user,
                text=text
            )
            
            # Определяем получателя
            if request.user == booking.renter:
                receiver = booking.item.owner
            else:
                receiver = booking.renter
            
            # Создаём уведомление для получателя
            Notification.objects.create(
                user=receiver,
                title=f'Новое сообщение от {request.user.username}',
                message=f'По поводу "{booking.item.name}": {text[:50]}',
                link=f'/chat/{booking.id}/',
                is_read=False
            )
            
            messages.success(request, 'Сообщение отправлено')
    
    messages_list = Message.objects.filter(booking=booking).order_by('created_at')
    
    for msg in messages_list:
        if msg.sender != request.user and not msg.is_read:
            msg.is_read = True
            msg.save()
    
    return render(request, 'chat_detail.html', {
        'booking': booking,
        'chat_messages': messages_list
    })