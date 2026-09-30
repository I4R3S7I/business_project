from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Необходимо указать email-адрес.')
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_stuff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):

    username = None
    email = models.EmailField('email', unique=True)
    is_company_owner = models.BooleanField('Владелец компании', default=False)
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        verbose_name='компания',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'
        db_table = 'user'
        constraints = [
            models.UniqueConstraint(
                fields=['company'],
                condition=models.Q(is_company_owner=True),
                name='one_owner_per_company',
                violation_error_message='У компании может быть только один владелец.',
            ),
            models.CheckConstraint(
                condition=models.Q(is_company_owner=False) | models.Q(company__isnull=False),
                name='owner_must_have_company',
                violation_error_message='Владелец должен быть привязан к компании.',
            ),
        ]

    def __str__(self):
        return self.email

    def clean(self):
        super().clean()
        if self.is_company_owner and not self.company_id:
            raise ValidationError(
                {'is_company_owner': 'Владелец компании должен быть привязан к компании.'}
            )
        if self.is_company_owner and self.company_id:
            others=User.objects.filter(company_id=self.company_id, is_company_owner=True)
            if self.pk:
                others = others.exclude(pk=self.pk)
            if others.exists():
                raise ValidationError(
                    {'is_company_owner': 'У компании может быть только один владелец.'}
                )

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email).lower()
        super().save(*args, **kwargs)
