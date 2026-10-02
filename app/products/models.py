from django.db import models
from django.core.validators import MinValueValidator


class Product(models.Model):
    '''Товар на складе.'''

    storage = models.ForeignKey(
        'storage.Storage',
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='склад',
    )
    title = models.CharField('название', max_length=255)
    description = models.TextField('описание', blank=True)
    quantity = models.PositiveIntegerField(
        'количество',
        default=0,
        help_text='Через API нельзя изменить. Изменить только можно путем поставок и продаж.',
    )
    purchase_price = models.DecimalField(
        'закупочная цена',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    sale_price = models.DecimalField(
        'цена продажи',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField('создан', auto_now_add=True)
    updated_at = models.DateTimeField('обновлен', auto_now=True)

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'
        db_table = 'product'
        ordering = ['title']
        constraints = [
            models.UniqueConstraint(
                fields=['storage', 'title'],
                name='unique_product_title_per_storage',
                violation_error_message='Такой товар уже есть на складе.'
            ),
        ]

    def __str__(self):
        return self.title

