from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_autp_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Пользователи'
