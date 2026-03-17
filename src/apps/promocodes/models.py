from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
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

    def clean(self):
        """Проверка промокода."""
        if not self.is_active:
            raise ValidationError("Этот промокод деактивирован.")

        if self.valid_until and self.valid_until < timezone.now():
            raise ValidationError("Срок действия промокода истек.")

        if self.current_uses >= self.max_uses:
            raise ValidationError(
                "Максимальное количество использований этого промокода исчерпано."
            )

    def is_applicable_to_product(self, product):
        """Проверка: можно ли применить этот код к конкретному товару."""
        if not product.is_promo_eligible:
            return False

        allowed_categories = self.categories.all()
        if allowed_categories.exists() and product.category not in allowed_categories:
            return False
        return True

    def __str__(self):
        return f"{self.code} (-{self.discount_percent}%)"
