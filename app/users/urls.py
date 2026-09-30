from django.urls import path

from users.views import LoginView, MeView, RefreshView, RegisterView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/token/', LoginView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', RefreshView.as_view(), name='token_refresh'),
    path('users/me/', MeView.as_view(), name='me'),
]