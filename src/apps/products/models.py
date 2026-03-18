from django.core.validators import MinValueValidator
from django.db import models

from src.core.models import BaseModel


class Category(BaseModel):
    name = models.CharField(
        max_length=100,
        verbose_name="Название",
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]
        db_table = "categories"

    def __str__(self):
        return self.name


class Product(BaseModel):
    name = models.CharField(
        max_length=255,
        verbose_name="Товар",
    )
    category = models.ForeignKey(
        "Category",
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Категория",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена",
        help_text="Цена в рублях",
    )
    stock = models.PositiveIntegerField(
        default=0,
        verbose_name="Остаток на складе",
        help_text="Количество единиц товара, доступных для заказа",
        validators=[MinValueValidator(0)],
    )
    is_promo_eligible = models.BooleanField(
        default=True,
        verbose_name="Доступен для промокодов",
        help_text="Флаг определяет, можно ли применить скидку к этому товару",
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["name"]
        db_table = "products"

    def __str__(self):
        return self.name
