from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_autp_field = 'django.db.models.BigAutoField'
    name = 'app.users'
    verbose_name = 'Пользователь'
    verbose_name_plural = 'Пользователи'
