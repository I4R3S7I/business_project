from django.db import models
from django.conf import settings


class Sale(models.Model):
    '''Продажа товаров компании покупателю.'''

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='sales',
        verbose_name='компания',
    )
    buyer_name = models.CharField('имя покупателя', max_length=255)
    sale_date = models.DateField('дата продажи', blank=True, null=True)
    products = models.ManyToManyField(
        'products.Product',
        through='ProductSale',
        related_name='sales',
        verbose_name='товары',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales',
        verbose_name='кто оформил',
    )
    created_at = models.DateTimeField('создана', auto_now_add=True)

    class Meta:
        verbose_name = 'продажа'
        verbose_name_plural = 'продажи'
        db_table = 'sale'
        ordering = ['-sale_date', '-id']

    def __str__(self):
        return f'Продажа {self.pk} - {self.buyer_name}'


class ProductSale(models.Model):
    '''Позиция продажи: товар и сколько единиц продано.'''

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='product_sales',
        verbose_name='продажа',
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='sale_items',
        verbose_name='товар'
    )
    quantity = models.PositiveIntegerField('количество')

    class Meta:
        verbose_name = 'позиция продажи'
        verbose_name_plural = 'позиции продажи'
        db_table = 'product_sale'
        constraints = [
            models.UniqueConstraint(
                fields=['sale', 'product'],
                name='unique_product_per_sale',
                violation_error_message='Товар уже есть в этой продаже.',
            ),
        ]

    def __str__(self):
        return f'{self.product} x {self.quantity}'
