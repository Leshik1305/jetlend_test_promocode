from django.conf import settings
from django.db import models

from src.apps.products.models import Product
from src.apps.promocodes.models import PromoCode
from src.core.models import BaseModel


class Order(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Покупатель",
        related_name="orders",
    )
    promocode = models.ForeignKey(
        PromoCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Промокод",
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Итоговая цена",
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        db_table = "orders"

    @property
    def total_price_before_discount(self):
        return sum(item.price_at_purchase * item.quantity for item in self.items.all())

    @property
    def total_discount_amount(self):
        return self.total_price_before_discount - self.total_amount

    def __str__(self):
        return f"Заказ №{self.id} | {self.user.username}"


class OrderItem(BaseModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество",
    )
    price_at_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"
        db_table = "order_items"
