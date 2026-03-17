import json
from django.http import JsonResponse
from django.views import View
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import Order, OrderItem
from src.apps.products.models import Product
from src.apps.promocodes.models import PromoCode

User = get_user_model()


@method_decorator(csrf_exempt, name="dispatch")
class OrderCreateView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        user_id = data.get("user_id")
        goods_data = data.get("goods", [])
        promo_code_str = data.get("promo_code")

        user = get_object_or_404(User, id=user_id)

        # Находим промокод
        promo = None
        if promo_code_str:
            promo = PromoCode.objects.filter(code=promo_code_str).first()

        with transaction.atomic():
            # Создаем болванку заказа
            order = Order.objects.create(user=user, promocode=promo, total_amount=0)

            response_goods = []
            total_price = 0
            total_discount_sum = 0

            for item in goods_data:
                product = Product.objects.get(id=item["good_id"])
                qty = item["quantity"]

                price = product.price
                discount_value = 0

                # Если промокод подходит к товару (по категориям или если их нет)
                if promo and (
                    not promo.categories.exists()
                    or promo.categories.filter(id=product.category_id).exists()
                ):
                    discount_value = (price * promo.discount_percent) / 100

                item_total = (price - discount_value) * qty

                # Сохраняем в БД
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=qty,
                    price_at_purchase=price,
                    discount_amount=discount_value,
                )

                # Собираем данные для ответа
                response_goods.append(
                    {
                        "good_id": product.id,
                        "quantity": qty,
                        "price": float(price),
                        "discount": (
                            str(promo.discount_percent / 100)
                            if discount_value > 0
                            else "0"
                        ),
                        "total": float(item_total),
                    }
                )

                total_price += price * qty
                total_discount_sum += discount_value * qty

            # Обновляем заказ
            final_total = total_price - total_discount_sum
            order.total_amount = final_total
            order.save()

            if promo:
                promo.current_uses += 1
                promo.save()

            # Формируем ответ по вашему примеру
            return JsonResponse(
                {
                    "user_id": user.id,
                    "order_id": order.id,
                    "goods": response_goods,
                    "price": float(total_price),
                    "discount": str(promo.discount_percent / 100) if promo else "0",
                    "total": float(final_total),
                },
                status=201,
            )
