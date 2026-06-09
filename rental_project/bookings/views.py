from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.http import JsonResponse
from items.models import Item
from .models import Booking
from notifications.models import Notification


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(renter=request.user).order_by('-created_at')

    now = timezone.now()
    for booking in bookings:
        if booking.status == 'confirmed' and booking.start_datetime <= now:
            booking.status = 'waiting_payment'
            booking.save()
        elif booking.status == 'in_progress' and booking.end_datetime < now:
            booking.status = 'waiting_return'
            booking.save()

    status_filter = request.GET.get('status', 'active')
    if status_filter and status_filter != 'all':
        bookings = bookings.filter(status=status_filter)

    all_bookings = Booking.objects.filter(renter=request.user)
    stats = {
        'pending': all_bookings.filter(status='pending').count(),
        'confirmed': all_bookings.filter(status='confirmed').count(),
        'waiting_payment': all_bookings.filter(status='waiting_payment').count(),
        'waiting_payment_confirmation': all_bookings.filter(status='waiting_payment_confirmation').count(),
        'in_progress': all_bookings.filter(status='in_progress').count(),
        'waiting_return': all_bookings.filter(status='waiting_return').count(),
        'waiting_refund': all_bookings.filter(status='waiting_refund').count(),
        'waiting_refund_confirmation': all_bookings.filter(status='waiting_refund_confirmation').count(),
        'completed': all_bookings.filter(status='completed').count(),
        'cancelled': all_bookings.filter(status='cancelled').count(),
        'disputed': all_bookings.filter(status='disputed').count(),
    }

    return render(request, 'bookings/my_bookings.html', {
        'bookings': bookings,
        'stats': stats,
        'current_filter': status_filter
    })


@login_required
def owner_bookings(request):
    bookings = Booking.objects.filter(item__owner=request.user).order_by('-created_at')

    now = timezone.now()
    for booking in bookings:
        if booking.status == 'in_progress' and booking.end_datetime < now:
            booking.status = 'waiting_return'
            booking.save()

    status_filter = request.GET.get('status', 'pending')
    if status_filter and status_filter != 'all':
        bookings = bookings.filter(status=status_filter)

    all_bookings = Booking.objects.filter(item__owner=request.user)
    stats = {
        'pending': all_bookings.filter(status='pending').count(),
        'confirmed': all_bookings.filter(status='confirmed').count(),
        'waiting_payment': all_bookings.filter(status='waiting_payment').count(),
        'waiting_payment_confirmation': all_bookings.filter(status='waiting_payment_confirmation').count(),
        'in_progress': all_bookings.filter(status='in_progress').count(),
        'waiting_return': all_bookings.filter(status='waiting_return').count(),
        'waiting_refund': all_bookings.filter(status='waiting_refund').count(),
        'waiting_refund_confirmation': all_bookings.filter(status='waiting_refund_confirmation').count(),
        'completed': all_bookings.filter(status='completed').count(),
    }

    return render(request, 'bookings/owner_bookings.html', {
        'bookings': bookings,
        'stats': stats,
        'current_filter': status_filter
    })


@login_required
def create_booking(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if item.owner == request.user:
        messages.error(request, 'Вы не можете забронировать собственную вещь')
        return redirect('items:item_detail', item_id=item.id)

    if request.method == 'POST':
        try:
            start_datetime_str = request.POST.get('start_datetime')
            end_datetime_str = request.POST.get('end_datetime')

            start_datetime = datetime.fromisoformat(start_datetime_str)
            end_datetime = datetime.fromisoformat(end_datetime_str)

            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)

            if start_datetime < timezone.now():
                messages.error(request, 'Дата начала не может быть в прошлом')
                return redirect('items:item_detail', item_id=item.id)

            if end_datetime <= start_datetime:
                messages.error(request, 'Дата окончания должна быть позже даты начала')
                return redirect('items:item_detail', item_id=item.id)

            delta = end_datetime - start_datetime
            total_minutes = delta.total_seconds() / 60
            total_hours = total_minutes / 60

            price_per_hour = float(item.price_per_hour)
            deposit_amount = float(item.deposit_amount)
            total_amount = price_per_hour * total_hours

            if total_amount > 1000000:
                messages.error(request, 'Слишком большая сумма аренды. Максимум 1 000 000 ₽')
                return redirect('items:item_detail', item_id=item.id)

            booking = Booking.objects.create(
                item=item,
                renter=request.user,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                price_per_hour=price_per_hour,
                total_hours=total_hours,
                total_amount=total_amount,
                deposit_amount=deposit_amount,
                status='pending'
            )

            messages.success(request, f'Заявка на аренду "{item.name}" отправлена владельцу!')
            return redirect('bookings:booking_detail', booking_id=booking.id)

        except Exception as e:
            messages.error(request, f'Ошибка при создании бронирования: {str(e)}')
            return redirect('items:item_detail', item_id=item.id)

    return render(request, 'booking_form.html', {'item': item})


@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.renter and request.user != booking.item.owner:
        messages.error(request, 'У вас нет доступа')
        return redirect('home')

    return render(request, 'bookings/booking_detail.html', {'booking': booking})


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.renter != request.user:
        messages.error(request, 'Вы не можете отменить это бронирование')
        return redirect('bookings:my_bookings')

    if booking.status != 'pending':
        messages.error(request, 'Можно отменить только ожидающие подтверждения')
        return redirect('bookings:booking_detail', booking_id=booking_id)

    booking.status = 'cancelled'
    booking.save()

    Notification.objects.create(
        user=booking.item.owner,
        title='Бронирование отменено',
        message=f'Пользователь {request.user.username} отменил бронирование "{booking.item.name}".',
        link='/bookings/owner/',
        is_read=False
    )

    messages.success(request, 'Бронирование отменено')
    return redirect('bookings:my_bookings')


@login_required
def confirm_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.item.owner:
        messages.error(request, 'У вас нет прав')
        return redirect('bookings:owner_bookings')

    if booking.status != 'pending':
        messages.error(request, 'Бронирование уже обработано')
        return redirect('bookings:owner_bookings')

    booking.status = 'confirmed'
    booking.save()

    Notification.objects.create(
        user=booking.renter,
        title='Бронирование подтверждено',
        message=f'Владелец подтвердил бронирование "{booking.item.name}". Ожидайте начала аренды.',
        link='/bookings/my/',
        is_read=False
    )

    Notification.objects.create(
        user=booking.item.owner,
        title='Бронирование подтверждено',
        message=f'Вы подтвердили бронирование "{booking.item.name}" для {booking.renter.username}.',
        link='/bookings/owner/',
        is_read=False
    )

    messages.success(request, 'Бронирование подтверждено')
    return redirect('bookings:owner_bookings')


@login_required
def reject_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.item.owner:
        messages.error(request, 'У вас нет прав')
        return redirect('bookings:owner_bookings')

    if booking.status != 'pending':
        messages.error(request, 'Бронирование уже обработано')
        return redirect('bookings:owner_bookings')

    booking.status = 'rejected'
    booking.save()

    Notification.objects.create(
        user=booking.renter,
        title='Бронирование отклонено',
        message=f'Владелец отклонил бронирование "{booking.item.name}".',
        link='/bookings/my/',
        is_read=False
    )

    messages.warning(request, 'Бронирование отклонено')
    return redirect('bookings:owner_bookings')


@login_required
def confirm_receipt(request, booking_id):
    """Арендатор подтверждает получение → показываем QR для оплаты"""
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.renter != request.user:
        messages.error(request, 'Вы не можете подтвердить получение')
        return redirect('bookings:my_bookings')

    if booking.status != 'confirmed':
        messages.error(request, 'Можно подтвердить получение только для подтверждённой аренды')
        return redirect('bookings:my_bookings')

    if booking.rental_paid:
        messages.info(request, 'Аренда уже оплачена')
        return redirect('bookings:my_bookings')

    if request.method == 'POST':
        booking.renter_received = True
        booking.status = 'waiting_payment_confirmation'
        booking.save()

        # Уведомление владельцу — подтвердить оплату
        Notification.objects.create(
            user=booking.item.owner,
            title='Подтвердите оплату аренды',
            message=f'Арендатор {booking.renter.username} оплатил аренду "{booking.item.name}". Проверьте счёт и подтвердите оплату.',
            link=f'/bookings/confirm-payment/{booking.id}/',
            is_read=False
        )

        messages.success(request, 'Вы подтвердили получение вещи. Ожидайте подтверждения оплаты от владельца.')
        return redirect('bookings:my_bookings')

    total_payment = booking.total_amount + booking.deposit_amount
    qr_image_url = "https://quickchart.io/qr?text=https://c2c.cbrpay.ru/BS1I004KQF13O9AE9B4A159OC6L7IR0B&size=200&margin=2"
    recipient_name = booking.item.owner.get_full_name() or booking.item.owner.username

    return render(request, 'bookings/pay_rent_qr.html', {
        'booking': booking,
        'qr_image_url': qr_image_url,
        'amount': total_payment,
        'recipient_name': recipient_name
    })


@login_required
def confirm_payment(request, booking_id):
    """Владелец подтверждает, что деньги за аренду поступили"""
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.item.owner:
        messages.error(request, 'У вас нет прав')
        return redirect('home')

    if booking.status != 'waiting_payment_confirmation':
        messages.error(request, 'Нет ожидающих подтверждения платежей')
        return redirect('bookings:owner_bookings')

    if request.method == 'POST':
        decision = request.POST.get('decision')

        if decision == 'confirm':
            booking.payment_confirmed_by_owner = True
            booking.payment_confirmed_at = timezone.now()
            booking.status = 'in_progress'
            booking.save()

            Notification.objects.create(
                user=booking.renter,
                title='Оплата аренды подтверждена',
                message=f'Владелец подтвердил оплату аренды "{booking.item.name}". Аренда началась!',
                link='/bookings/my/',
                is_read=False
            )

            messages.success(request, 'Вы подтвердили оплату. Аренда началась.')
            return redirect('bookings:owner_bookings')

        elif decision == 'failed':
            booking.status = 'disputed'
            booking.save()

            Notification.objects.create(
                user=booking.renter,
                title='Проблема с оплатой',
                message=f'Владелец сообщил, что оплата за "{booking.item.name}" не поступила. Открыт спор.',
                link='/bookings/my/',
                is_read=False
            )

            messages.warning(request, 'Оплата не подтверждена. Открыт спор.')
            return redirect('bookings:owner_bookings')

    return render(request, 'bookings/confirm_payment.html', {'booking': booking})


@login_required
def return_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.renter != request.user:
        messages.error(request, 'Вы не можете подтвердить возврат')
        return redirect('bookings:my_bookings')

    if booking.status != 'in_progress':
        messages.error(request, 'Можно подтвердить возврат только для активной аренды')
        return redirect('bookings:my_bookings')

    booking.status = 'waiting_return'
    booking.save()

    Notification.objects.create(
        user=booking.item.owner,
        title='Возврат вещи',
        message=f'Арендатор вернул "{booking.item.name}". Проверьте состояние.',
        link='/bookings/owner/',
        is_read=False
    )

    messages.success(request, 'Вы подтвердили возврат. Ожидайте проверки владельца.')
    return redirect('bookings:my_bookings')


@login_required
def confirm_return_no_damage(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.item.owner:
        messages.error(request, 'У вас нет прав')
        return redirect('bookings:owner_bookings')

    if booking.status != 'waiting_return':
        messages.error(request, 'Нет ожидающих подтверждения возвратов')
        return redirect('bookings:owner_bookings')

    if request.method == 'POST':
        booking.owner_return_confirmed = True
        booking.status = 'waiting_refund_confirmation'
        booking.save()

        Notification.objects.create(
            user=booking.renter,
            title='Подтвердите получение залога',
            message=f'Владелец вернул вещь "{booking.item.name}" без повреждений. Проверьте счёт и подтвердите получение залога {booking.deposit_amount:.2f} ₽.',
            link=f'/bookings/confirm-refund/{booking.id}/',
            is_read=False
        )

        messages.success(request, 'Возврат подтверждён. Арендатор должен подтвердить получение залога.')
        return redirect('bookings:owner_bookings')

    qr_image_url = "https://quickchart.io/qr?text=https://c2c.cbrpay.ru/BS1I004KQF13O9AE9B4A159OC6L7IR0B&size=200&margin=2"
    recipient_name = booking.renter.get_full_name() or booking.renter.username

    return render(request, 'bookings/refund_qr.html', {
        'booking': booking,
        'qr_image_url': qr_image_url,
        'amount': booking.deposit_amount,
        'recipient_name': recipient_name
    })


@login_required
def confirm_refund(request, booking_id):
    """Арендатор подтверждает, что залог вернулся"""
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.renter:
        messages.error(request, 'У вас нет прав')
        return redirect('home')

    if booking.status != 'waiting_refund_confirmation':
        messages.error(request, 'Нет ожидающих подтверждения возврата залога')
        return redirect('bookings:my_bookings')

    if request.method == 'POST':
        decision = request.POST.get('decision')

        if decision == 'confirm':
            booking.refund_confirmed_by_renter = True
            booking.refund_confirmed_at = timezone.now()
            booking.deposit_returned = True
            booking.status = 'completed'
            booking.save()

            Notification.objects.create(
                user=booking.item.owner,
                title='Залог получен арендатором',
                message=f'Арендатор подтвердил получение залога {booking.deposit_amount:.2f} ₽ за "{booking.item.name}". Аренда завершена.',
                link='/bookings/owner/',
                is_read=False
            )

            messages.success(request, 'Вы подтвердили получение залога. Аренда завершена!')
            return redirect('bookings:my_bookings')

        elif decision == 'failed':
            booking.status = 'disputed'
            booking.deposit_frozen = True
            booking.dispute_created_at = timezone.now()
            booking.save()

            Notification.objects.create(
                user=booking.item.owner,
                title='Спор о возврате залога',
                message=f'Арендатор сообщил, что залог {booking.deposit_amount:.2f} ₽ за "{booking.item.name}" не поступил. Открыт спор.',
                link='/bookings/owner/',
                is_read=False
            )

            messages.warning(request, 'Вы сообщили, что залог не поступил. Открыт спор.')
            return redirect('bookings:my_bookings')

    return render(request, 'bookings/confirm_refund.html', {'booking': booking})


@login_required
def refund_deposit(request, booking_id):
    """Страница для возврата залога (по решению спора)"""
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.item.owner:
        messages.error(request, 'У вас нет прав')
        return redirect('home')

    if request.method == 'POST':
        booking.deposit_returned = True
        booking.status = 'waiting_refund_confirmation'
        booking.save()

        Notification.objects.create(
            user=booking.renter,
            title='Подтвердите получение залога',
            message=f'Владелец вернул залог {booking.deposit_amount:.2f} ₽ за "{booking.item.name}". Проверьте счёт.',
            link=f'/bookings/confirm-refund/{booking.id}/',
            is_read=False
        )

        messages.success(request, 'Залог отмечен как возвращённый. Ожидайте подтверждения от арендатора.')
        return redirect('bookings:owner_bookings')

    qr_image_url = "https://quickchart.io/qr?text=https://c2c.cbrpay.ru/BS1I004KQF13O9AE9B4A159OC6L7IR0B&size=200&margin=2"
    recipient_name = booking.renter.get_full_name() or booking.renter.username

    return render(request, 'bookings/refund_qr.html', {
        'booking': booking,
        'qr_image_url': qr_image_url,
        'amount': booking.deposit_amount,
        'recipient_name': recipient_name
    })


@login_required
def report_damage(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.item.owner:
        messages.error(request, 'У вас нет прав')
        return redirect('bookings:owner_bookings')

    if booking.status != 'waiting_return':
        messages.error(request, 'Нельзя оформить спор для этого бронирования')
        return redirect('bookings:owner_bookings')

    if request.method == 'POST':
        damage_description = request.POST.get('damage_description', '')

        booking.damage_description = damage_description
        booking.status = 'disputed'
        booking.deposit_frozen = True
        booking.dispute_created_at = timezone.now()

        if request.FILES.get('damage_photo'):
            booking.damage_photo = request.FILES['damage_photo']
        if request.FILES.get('damage_video'):
            booking.damage_video = request.FILES['damage_video']

        booking.save()

        Notification.objects.create(
            user=booking.renter,
            title='Открыт спор по возврату',
            message=f'Владелец сообщил о повреждении "{booking.item.name}".',
            link='/bookings/my/',
            is_read=False
        )

        Notification.objects.create(
            user=booking.item.owner,
            title='Спор открыт',
            message=f'Спор по "{booking.item.name}" открыт.',
            link='/bookings/owner/',
            is_read=False
        )

        messages.warning(request, 'Спор открыт. Ожидайте решения модератора.')
        return redirect('bookings:owner_bookings')

    return render(request, 'bookings/report_damage.html', {'booking': booking})


@login_required
def dispute_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.renter and request.user != booking.item.owner:
        messages.error(request, 'У вас нет доступа')
        return redirect('home')

    return render(request, 'bookings/dispute_detail.html', {'booking': booking})


@login_required
def dispute_accept(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.renter:
        messages.error(request, 'У вас нет прав')
        return redirect('bookings:my_bookings')

    if booking.status != 'disputed':
        messages.error(request, 'Спор уже решён')
        return redirect('bookings:my_bookings')

    booking.deposit_to_owner = True
    booking.deposit_returned = False
    booking.deposit_frozen = False
    booking.status = 'completed'
    booking.dispute_resolved_at = timezone.now()
    booking.save()

    Notification.objects.create(
        user=booking.item.owner,
        title='Спор решён',
        message=f'Арендатор признал вину за повреждение "{booking.item.name}". Залог {booking.deposit_amount:.2f} ₽ остаётся у вас.',
        link='/bookings/owner/',
        is_read=False
    )

    Notification.objects.create(
        user=booking.renter,
        title='Залог удержан',
        message=f'Вы признали вину за повреждение "{booking.item.name}". Залог {booking.deposit_amount:.2f} ₽ удержан.',
        link='/bookings/my/',
        is_read=False
    )

    messages.success(request, f'Вы признали вину. Залог {booking.deposit_amount:.2f} ₽ остаётся у владельца.')
    return redirect('bookings:my_bookings')


@login_required
def dispute_contest(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.renter:
        messages.error(request, 'У вас нет прав')
        return redirect('bookings:my_bookings')

    if booking.status != 'disputed':
        messages.error(request, 'Спор уже решён')
        return redirect('bookings:my_bookings')

    booking.needs_moderation = True
    booking.save()

    Notification.objects.create(
        user=booking.item.owner,
        title='Спор оспорен',
        message=f'Арендатор оспорил вашу жалобу по "{booking.item.name}". Решение будет принято модератором.',
        link='/bookings/owner/',
        is_read=False
    )

    messages.info(request, 'Вы оспорили жалобу. Решение примет модератор в течение 24 часов.')
    return redirect('bookings:my_bookings')