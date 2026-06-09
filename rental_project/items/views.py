from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Item, Category
from django.http import Http404

def catalog(request):
    items = Item.objects.filter(status='available')
    categories = Category.objects.all()

    category_id = request.GET.get('category')
    search = request.GET.get('search')

    if category_id and category_id.isdigit():
        items = items.filter(category_id=int(category_id))
    if search:
        items = items.filter(name__icontains=search)

    items = items.order_by('-created_at')

    return render(request, 'catalog.html', {
        'items': items,
        'categories': categories
    })

def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    return render(request, 'item_detail.html', {'item': item})

@login_required
def my_items(request):
    items = Item.objects.filter(owner=request.user).order_by('-created_at')
    categories = Category.objects.all()
    return render(request, 'my_items.html', {
        'items': items,
        'categories': categories
    })

@login_required
def add_item(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        city = request.POST.get('city')
        price_per_hour = request.POST.get('price_per_hour')
        deposit_amount = request.POST.get('deposit_amount', 0)
        category_id = request.POST.get('category')
        main_photo = request.FILES.get('main_photo')

        if not all([name, description, city, price_per_hour, category_id]):
            messages.error(request, 'Заполните все обязательные поля')
            return redirect('/items/my-items/')

        try:
            price_per_hour = float(price_per_hour)
            deposit_amount = float(deposit_amount) if deposit_amount else 0
        except ValueError:
            messages.error(request, 'Цена должна быть числом')
            return redirect('/items/my-items/')

        if price_per_hour < 0:
            messages.error(request, 'Цена не может быть отрицательной')
            return redirect('/items/my-items/')

        if price_per_hour > 100000:
            messages.error(request, 'Цена не может превышать 100 000 ₽ в час')
            return redirect('/items/my-items/')

        if deposit_amount < 0:
            messages.error(request, 'Залог не может быть отрицательным')
            return redirect('/items/my-items/')

        if deposit_amount > 500000:
            messages.error(request, 'Залог не может превышать 500 000 ₽')
            return redirect('/items/my-items/')

        if price_per_hour == 0:
            messages.warning(request, 'Вы указали цену 0 ₽/час — это бесплатная аренда')

        Item.objects.create(
            owner=request.user,
            name=name,
            description=description,
            city=city,
            price_per_hour=price_per_hour,
            deposit_amount=deposit_amount,
            category_id=category_id,
            main_photo=main_photo,
            status='available'
        )

        messages.success(request, f'Вещь "{name}" успешно добавлена!')
        return redirect('/items/my-items/')

    return redirect('/items/my-items/')

@login_required
def delete_item(request, item_id):
    try:
        item = get_object_or_404(Item, id=item_id, owner=request.user)
        item.delete()
        messages.success(request, 'Вещь удалена')
    except Http404:
        messages.warning(request, 'Эта вещь уже была удалена')
    return redirect('/items/my-items/')

@login_required
def edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, owner=request.user)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        city = request.POST.get('city')
        price_per_hour = request.POST.get('price_per_hour')
        deposit_amount = request.POST.get('deposit_amount', 0)
        category_id = request.POST.get('category')
        main_photo = request.FILES.get('main_photo')

        if not all([name, description, city, price_per_hour, category_id]):
            messages.error(request, 'Заполните все обязательные поля')
            return redirect('/items/my-items/')

        try:
            price_per_hour = float(price_per_hour)
            deposit_amount = float(deposit_amount) if deposit_amount else 0
        except ValueError:
            messages.error(request, 'Цена должна быть числом')
            return redirect('/items/my-items/')

        if price_per_hour < 0:
            messages.error(request, 'Цена не может быть отрицательной')
            return redirect('/items/my-items/')

        if price_per_hour > 100000:
            messages.error(request, 'Цена не может превышать 100 000 ₽ в час')
            return redirect('/items/my-items/')

        if deposit_amount < 0:
            messages.error(request, 'Залог не может быть отрицательным')
            return redirect('/items/my-items/')

        if deposit_amount > 500000:
            messages.error(request, 'Залог не может превышать 500 000 ₽')
            return redirect('/items/my-items/')

        item.name = name
        item.description = description
        item.city = city
        item.price_per_hour = price_per_hour
        item.deposit_amount = deposit_amount
        item.category_id = category_id

        if main_photo:
            item.main_photo = main_photo

        item.save()

        messages.success(request, f'Вещь "{name}" успешно обновлена!')
        return redirect('/items/my-items/')

    return redirect('/items/my-items/')

@login_required
def toggle_status(request, item_id):
    item = get_object_or_404(Item, id=item_id, owner=request.user)

    if item.status == 'available':
        item.status = 'unavailable'
        messages.info(request, f'Вещь "{item.name}" теперь недоступна')
    else:
        item.status = 'available'
        messages.success(request, f'Вещь "{item.name}" снова доступна')

    item.save()
    return redirect('/items/my-items/')

@login_required
def my_rented_items(request):
    from bookings.models import Booking

    active_bookings = Booking.objects.filter(
        item__owner=request.user,
        status__in=['confirmed', 'active']
    ).select_related('item', 'renter')

    return render(request, 'my_rented_items.html', {
        'active_bookings': active_bookings
    })