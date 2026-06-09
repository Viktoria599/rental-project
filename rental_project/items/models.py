from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from django.core.validators import FileExtensionValidator

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Item(models.Model):
    STATUS_CHOICES = [
        ('available', 'Доступна'),
        ('busy', 'Занята'),
        ('unavailable', 'Недоступна'),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='items')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    city = models.CharField(max_length=100)

    # Добавляем валидацию: от 0 до 100 000
    price_per_hour = models.FloatField(
        default=0,
        validators=[
            MinValueValidator(0, 'Цена не может быть отрицательной'),
            MaxValueValidator(100000, 'Цена не может превышать 100 000 ₽ в час')
        ]
    )

    deposit_amount = models.FloatField(
        default=0,
        validators=[
            MinValueValidator(0, 'Залог не может быть отрицательным'),
            MaxValueValidator(500000, 'Залог не может превышать 500 000 ₽')
        ]
    )

    main_photo = models.ImageField(
        upload_to='items/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name