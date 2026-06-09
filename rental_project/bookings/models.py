from django.db import models
from django.conf import settings
from items.models import Item


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждена'),
        ('waiting_payment', 'Ожидает оплаты'),
        ('waiting_payment_confirmation', 'Ожидает подтверждения оплаты'),
        ('in_progress', 'В процессе аренды'),
        ('waiting_return', 'Ожидает возврата'),
        ('waiting_refund', 'Ожидает возврата залога'),
        ('waiting_refund_confirmation', 'Ожидает подтверждения возврата залога'),
        ('completed', 'Завершена'),
        ('rejected', 'Отклонена'),
        ('cancelled', 'Отменена'),
        ('disputed', 'Спор'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    renter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')

    price_per_hour = models.FloatField(default=0)
    total_hours = models.FloatField(default=0)
    total_amount = models.FloatField(default=0)
    deposit_amount = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    needs_moderation = models.BooleanField(default=False)
    rental_paid = models.BooleanField(default=False)
    review_given_by_renter = models.BooleanField(default=False)
    review_given_by_owner = models.BooleanField(default=False)

    renter_received = models.BooleanField(default=False)
    owner_return_confirmed = models.BooleanField(default=False)

    # Поля для залога
    deposit_frozen = models.BooleanField(default=False)
    deposit_returned = models.BooleanField(default=False)
    deposit_to_owner = models.BooleanField(default=False)

    # Новые поля для подтверждения платежей
    payment_confirmed_by_owner = models.BooleanField(default=False)
    payment_confirmed_at = models.DateTimeField(blank=True, null=True)
    refund_confirmed_by_renter = models.BooleanField(default=False)
    refund_confirmed_at = models.DateTimeField(blank=True, null=True)

    # Поля для спора
    damage_description = models.TextField(blank=True, null=True)
    damage_photo = models.ImageField(upload_to='damages/', blank=True, null=True)
    damage_video = models.FileField(upload_to='damages/', blank=True, null=True)
    dispute_created_at = models.DateTimeField(blank=True, null=True)
    dispute_resolved_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        delta = self.end_datetime - self.start_datetime
        total_minutes = delta.total_seconds() / 60

        self.total_hours = total_minutes / 60
        self.total_amount = (self.price_per_hour / 60) * total_minutes

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.name} - {self.renter.username}"