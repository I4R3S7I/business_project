from django.db import models


class Company(models.Model):
    '''Компания. У компании один владелец'''

    name = models.CharField('Название', max_length=255, unique=True)
    inn = models.CharField('ИНН', max_length=12, unique=True)
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        verbose_name = 'компания'
        verbose_name_plural = 'компании'
        db_table = 'company'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_owner(self):
        if not hasattr(self, '_owner_cache'):
            self._owner_cache = self.members.filter(is_company_owner=True).first()
        return self._owner_cache
