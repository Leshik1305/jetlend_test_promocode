from django.db import transaction
from rest_framework.exceptions import ValidationError

from src.apps.orders.models import Order, OrderItem
from src.apps.products.models import Product
from src.apps.promocodes.models import PromoCode


class OrderService:
    """Сервис для обработки бизнес-логики при создании заказа."""

    @staticmethod
    @transaction.atomic
    def create_order(user, goods_data, promocode=None):
        promo = None
        if promocode and promocode.strip():
            promo = PromoCode.objects.select_for_update().filter(code=promocode).first()
            if not promo:
                raise ValidationError({"promo_code": "Промокод не найден"})

            is_valid, message = promo.is_valid_status()
            if not is_valid:
                raise ValidationError({"promo_code": message})

            if Order.objects.filter(user=user, promocode=promo).exists():
                raise ValidationError(
                    {"promo_code": "Вы уже использовали этот промокод"}
                )

        order = Order.objects.create(user=user, promocode=promo, total_amount=0)

        total_price = 0
        final_total_price = 0

        for item in goods_data:
            product = Product.objects.select_for_update().get(id=item["good_id"])
            qty = item["quantity"]

            if product.stock < qty:
                raise ValidationError(f"Недостаточно товара: {product.name}")

            price = product.price
            discount_per_item = 0

            if promo and promo.is_applicable_to_product(product):
                discount_per_item = (price * promo.discount_percent) / 100

            total_price += price * qty
            final_total_price += (price - discount_per_item) * qty

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=qty,
                price_at_purchase=price,
                discount_amount=discount_per_item,
            )

            product.stock -= qty
            product.save()

        order.total_amount = final_total_price
        order.save()

        if promo:
            promo.current_uses += 1
            promo.save()

        return order
