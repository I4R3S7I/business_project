from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.models import User
from users.serializers import RegisterSerializer, UserSerializer


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get(self.username_field)
        if isinstance(email, str):
            attrs[self.username_field] = email.strip().lower()
        return super().validate(attrs)


@extend_schema(tags=['Аутентификация'], summary='Регстрация пользователя')
class RegisterView(generics.CreateAPIView):
    '''Создает пользователя с уникальным email. Пароль в ответ не возвращается'''

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema_view(post=extend_schema(tags=['Аутентификация'], summary='Вход (JWT)'))
class LoginView(TokenObtainPairView):
    '''Возвращает access и refresh токены. В теле запроса email и password.'''

    serializer_class = EmailTokenObtainPairSerializer


@extend_schema_view(post=extend_schema(tags=['Аутентификация'], summary='Обновление access токена'))
class RefreshView(TokenRefreshView):
    '''Принимает refresh токен и возвращает новый access токен.'''


@extend_schema(tags=['Аутентификация'], summary='Текущий пользователь')
class MeView(generics.RetrieveAPIView):
    '''Профиль пользователя, который выполнил запрос.'''

    serializer_class = UserSerializer

    def get_object(self):
        return User.objects.select_related('company').get(pk=self.request.user.pk)