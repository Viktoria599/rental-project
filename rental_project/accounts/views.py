from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal, InvalidOperation
import json
import re
from .models import User, Review
from bookings.models import Booking
from notifications.models import Notification
from .forms import CustomUserCreationForm


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.get_display_name()}!')
            return redirect('/items/')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.get_display_name()}!')
            return redirect('/items/')
        else:
            messages.error(request, 'Неверный email или пароль')
            return render(request, 'login.html')

    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('/items/')


@login_required
def profile(request, username=None):
    if username:
        reviewed_user = get_object_or_404(User, username=username)
    else:
        reviewed_user = request.user
    return render(request, 'profile.html', {'reviewed_user': reviewed_user})


@login_required
def profile_edit(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')[:50]
        user.last_name = request.POST.get('last_name', '')[:50]
        user.city = request.POST.get('city', '')[:100]
        user.username = request.POST.get('username', '')[:150]

        phone = request.POST.get('phone', '')
        import re
        cleaned_phone = re.sub(r'[^\d\+]', '', phone)
        if len(cleaned_phone) <= 20:
            user.phone = cleaned_phone

        user.save()
        messages.success(request, 'Профиль успешно обновлен!')
        return redirect('profile')

    return render(request, 'profile_edit.html', {'user': request.user})


@login_required
def leave_review(request, username):
    reviewed_user = get_object_or_404(User, username=username)

    if request.user == reviewed_user:
        messages.error(request, "Вы не можете оставить отзыв самому себе.")
        return redirect('profile', username=request.user.username)

    booking_id = request.GET.get('booking')

    if not booking_id:
        messages.error(request, "Отзыв можно оставить только после завершённой аренды.")
        return redirect('profile', username=reviewed_user.username)

    booking = get_object_or_404(Booking, id=booking_id)

    if booking.status != 'completed':
        messages.error(request, "Отзыв можно оставить только после завершения аренды.")
        return redirect('profile', username=reviewed_user.username)

    if request.user not in [booking.renter, booking.item.owner]:
        messages.error(request, "Вы не участвовали в этой аренде.")
        return redirect('profile', username=reviewed_user.username)

    if request.user == booking.renter and booking.review_given_by_renter:
        messages.error(request, "Вы уже оставили отзыв владельцу.")
        return redirect('profile', username=reviewed_user.username)

    if request.user == booking.item.owner and booking.review_given_by_owner:
        messages.error(request, "Вы уже оставили отзыв арендатору.")
        return redirect('profile', username=reviewed_user.username)

    existing_review = Review.objects.filter(reviewer=request.user, reviewed_user=reviewed_user).first()

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        if existing_review:
            existing_review.rating = rating
            existing_review.comment = comment
            existing_review.save()
            messages.success(request, "Ваш отзыв был обновлён.")
        else:
            Review.objects.create(
                reviewer=request.user,
                reviewed_user=reviewed_user,
                rating=rating,
                comment=comment
            )
            messages.success(request, "Спасибо за ваш отзыв!")

        if request.user == booking.renter:
            booking.review_given_by_renter = True
        elif request.user == booking.item.owner:
            booking.review_given_by_owner = True
        booking.save()

        return redirect('profile', username=reviewed_user.username)

    context = {
        'reviewed_user': reviewed_user,
        'existing_review': existing_review,
    }
    return render(request, 'accounts/leave_review.html', context)


@login_required
def moderator_panel(request):
    if not request.user.is_moderator and not request.user.is_superuser:
        messages.error(request, "У вас нет доступа к этой странице.")
        return redirect('home')

    disputes = Booking.objects.filter(status='disputed').order_by('-dispute_created_at')
    pending_disputes = disputes.filter(needs_moderation=True)
    resolved_disputes = Booking.objects.filter(
        status='completed',
        dispute_resolved_at__isnull=False
    ).order_by('-dispute_resolved_at')[:20]

    context = {
        'disputes': disputes,
        'pending_disputes': pending_disputes,
        'resolved_disputes': resolved_disputes,
    }
    return render(request, 'accounts/moderator_panel.html', context)


@login_required
def resolve_dispute(request, booking_id):
    if not request.user.is_moderator and not request.user.is_superuser:
        messages.error(request, "У вас нет прав.")
        return redirect('home')

    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        decision = request.POST.get('decision')
        moderator_comment = request.POST.get('moderator_comment', '')

        if decision == 'owner_wins':
            booking.deposit_to_owner = True
            booking.status = 'completed'
            messages.success(request, f"Спор решён в пользу владельца. Залог {booking.deposit_amount} ₽ остаётся у владельца.")

        elif decision == 'renter_wins':
            renter = booking.renter
            owner = booking.item.owner
            deposit_amount = booking.deposit_amount

            booking.deposit_returned = True
            booking.deposit_to_owner = False
            messages.success(request, f"Спор решён в пользу арендатора. Владельцу необходимо вернуть залог {deposit_amount} ₽ арендатору.")

        elif decision == 'moderation_needed':
            booking.needs_moderation = True
            messages.info(request, "Спор отправлен на дополнительную проверку.")
            return redirect('moderator_panel')

        booking.status = 'completed'
        booking.dispute_resolved_at = timezone.now()
        booking.moderator_comment = moderator_comment
        booking.save()

        Notification.objects.create(
            user=booking.renter,
            title='Решение по спору',
            message=f'Модератор принял решение по спору "{booking.item.name}".',
            link='/bookings/my/',
            is_read=False
        )

        Notification.objects.create(
            user=booking.item.owner,
            title='Решение по спору',
            message=f'Модератор принял решение по спору "{booking.item.name}".',
            link='/bookings/owner/',
            is_read=False
        )

        # Если решение в пользу арендатора — отправляем владельцу уведомление с QR для возврата залога
        if decision == 'renter_wins':
            Notification.objects.create(
                user=booking.item.owner,
                title='Верните залог арендатору',
                message=f'Решение спора в пользу арендатора. Перейдите по ссылке, чтобы вернуть залог {booking.deposit_amount} ₽.',
                link=f'/bookings/refund-deposit/{booking.id}/',
                is_read=False
            )

        return redirect('moderator_panel')

    return render(request, 'accounts/resolve_dispute.html', {'booking': booking})