from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    username = forms.CharField(required=False, label='Имя (как вас будут видеть)')
    
    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Этот email уже зарегистрирован')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        username = self.cleaned_data.get('username')
        if not username:
            username = self.cleaned_data['email'].split('@')[0]
        user.username = username
        if commit:
            user.save()
            # Сохраняем пароль через set_password (хеширование)
            user.set_password(self.cleaned_data['password1'])
            user.save()
        return user