from django.db import models

class Storage(models.Model):
    '''Склад компании.'''

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='storages',
        verbose_name='компания',
    )
    address = models.CharField('адрес', max_length=500)
    created_at = models.DateTimeField('создан', auto_now_add=True)
    updated_at = models.DateTimeField('обновлен', auto_now=True)

    class Meta:
        verbose_name = 'склад'
        verbose_name_plural = 'склады'
        db_table = 'storage'
        constraints = [
            models.UniqueConstraint(
                fields=['company'],
                name='one_storage_per_company',
                violation_error_message='У компании может быть только один склад.',
            ),
        ]

    def __str__(self):
        return self.address