from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('items/', include('items.urls')),
    path('bookings/', include('bookings.urls')),
    path('chat/', include('chat.urls')),
    path('notifications/', include('notifications.urls')),
    path('login/', accounts_views.user_login, name='login'),
    path('register/', accounts_views.register, name='register'),
    path('logout/', accounts_views.user_logout, name='logout'),
    path('profile/', accounts_views.profile, name='profile'),
    path('profile/edit/', accounts_views.profile_edit, name='profile_edit'),
    path('review/<str:username>/', views.leave_review, name='leave_review'),
    path('profile/', views.profile, name='profile'),  # свой профиль
    path('profile/<str:username>/', views.profile, name='profile'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)