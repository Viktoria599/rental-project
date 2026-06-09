from django import forms
from .models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['category', 'name', 'description', 'city', 'price_per_day', 'deposit_amount', 'main_photo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Электрическая дрель'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Опишите состояние, особенности, условия аренды...'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Москва'}),
            'price_per_day': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '500'}),
            'deposit_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1000 (если нужен залог)'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'main_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }