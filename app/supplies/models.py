from django.db import models
from django.conf import settings


class Supply(models.Model):
    '''Поставка товаров на склад от конкретного поставщика.'''

    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.PROTECT,
        related_name='supplies',
        verbose_name='поставщик',
    )
    delivery_date = models.DateField('дата поставки')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supplies',
        verbose_name='кто оформил',
    )
    created_at = models.DateTimeField('создана', auto_now_add=True)

    class Meta:
        verbose_name = 'поставка'
        verbose_name_plural = 'поставки'
        db_table = 'supply'
        ordering = ['-delivery_date', '-id']

    def __str__(self):
        return f'Поставка {self.pk} от {self.delivery_date}'


class SupplyProduct(models.Model):
    '''Позиция поставки: товар и сколько единиц пришло.'''

    supply = models.ForeignKey(
        Supply,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='поставка',
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='supply_items',
        verbose_name='товар',
    )
    quantity = models.PositiveIntegerField('количество')

    class Meta:
        verbose_name = 'позиция поставки'
        verbose_name_plural = 'позиции поставки'
        db_table = 'supply_product'
        constraints = [
            models.UniqueConstraint(
                fields=['supply', 'product'],
                name='unique_product_per_supply',
                violation_error_message='Товар уже есть в этой поставке.',
            ),
        ]

        def __str__(self):
            return f'{self.product} x {self.quantity}'