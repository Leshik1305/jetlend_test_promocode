from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from src.core.models import BaseModel


class PromoCode(BaseModel):
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Промокод",
    )
    discount_percent = models.PositiveIntegerField(
        verbose_name="Скидка (%)",
        help_text="Процент скидки от 1 до 100",
        validators=[
            MinValueValidator(1),
            MaxValueValidator(100),
        ],
    )
    valid_until = models.DateTimeField(verbose_name="Действует до")
    max_uses = models.PositiveIntegerField(
        verbose_name="Максимальное количество использований",
    )
    current_uses = models.PositiveIntegerField(
        default=0,
        verbose_name="Использовано раз",
    )

    categories = models.ManyToManyField(
        "products.Category",
        blank=True,
        related_name="promocodes",
        verbose_name="Ограничение по категориям",
    )

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"
        ordering = ["code"]
        db_table = "promocodes"

    def is_valid_status(self):
        """Проверка промокода."""
        if not self.is_active:
            return False, "Этот промокод деактивирован."

        if self.valid_until and self.valid_until < timezone.now():
            return False, "Срок действия промокода истек."

        if self.current_uses >= self.max_uses:
            return (
                False,
                "Максимальное количество использований этого промокода исчерпано.",
            )

        return True, ""

    def is_applicable_to_product(self, product):
        """Проверка: можно ли применить этот код к конкретному товару."""
        if not product.is_promo_eligible:
            return False

        allowed_ids = list(self.categories.values_list("id", flat=True))

        if not allowed_ids:
            return False

        return product.category_id in allowed_ids

    def clean(self):
        """Автоматически вызывается при создании через админку"""
        is_valid, message = self.is_valid_status()
        if not is_valid:
            raise ValidationError(message)

    def __str__(self):
        return f"{self.code} (-{self.discount_percent}%)"
