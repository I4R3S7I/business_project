from django.db import models


class Supplier(models.Model):
    '''Поставщик одной компании.'''

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='suppliers',
        verbose_name='компания',
    )
    name = models.CharField('название', max_length=255)
    inn = models.CharField('ИНН', max_length=12)
    created_at = models.DateTimeField('создан', auto_now_add=True)
    updated_at = models.DateTimeField('обновлен', auto_now=True)

    class Meta:
        verbose_name = 'поставщик'
        verbose_name_plural = 'поставщики'
        db_table = 'supplier'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'inn'],
                name='unique_supplier_per_company',
                violation_error_message='У компании уже есть поставщик с таким ИНН.',
            ),
        ]

    def __str__(self):
        return self.name
