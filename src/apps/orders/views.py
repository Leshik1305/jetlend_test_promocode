import json
from decimal import Decimal

from django.core.exceptions import ValidationError
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
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            goods_data = data.get("goods", [])
            promocode = data.get("promo_code")
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse(
                {"error": "Некорректный формат JSON в теле запроса"}, status=400
            )

        if not goods_data:
            return JsonResponse(
                {"error": "Список товаров не может быть пустым"}, status=400
            )

        user = get_object_or_404(User, id=user_id)

        try:
            with transaction.atomic():
                promo = None
                if promocode:
                    try:
                        promo = PromoCode.objects.select_for_update().get(
                            code=promocode
                        )
                        promo.clean()

                        if Order.objects.filter(user=user, promocode=promo).exists():
                            return JsonResponse(
                                {"error": "Вы уже использовали этот промокод"},
                                status=400,
                            )

                    except PromoCode.DoesNotExist:
                        return JsonResponse({"error": "Промокод не найден"}, status=404)
                    except ValidationError as e:
                        return JsonResponse({"error": e.message}, status=400)

                order = Order.objects.create(
                    user=user,
                    promocode=promo,
                    total_amount=Decimal("0.00"),
                )

                total_price = Decimal("0.00")
                total_final_price = Decimal("0.00")
                response_goods = []

                for item in goods_data:
                    good_id = item.get("good_id")
                    qty = int(item.get("quantity", 1))

                    try:
                        product = Product.objects.select_for_update().get(id=good_id)
                    except Product.DoesNotExist:
                        return JsonResponse(
                            {"error": f"Товар с ID {good_id} не найден в каталоге"},
                            status=404,
                        )
                    if product.stock < qty:
                        return JsonResponse(
                            {
                                "error": f"Недостаточно товара '{product.name}' на складе. В наличии: {product.stock}"
                            },
                            status=400,
                        )

                    price = product.price
                    discount_value = Decimal("0.00")
                    if promo and promo.is_applicable_to_product(product):
                        discount_value = (
                            price * Decimal(promo.discount_percent) / Decimal(100)
                        )

                    item_total = (price - discount_value) * qty
                    total_price += price * qty
                    total_final_price += item_total

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=qty,
                        price_at_purchase=price,
                        discount_amount=discount_value,
                    )

                    product.stock -= qty
                    product.save()

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

                order.total_amount = total_final_price
                order.save()

                if promo:
                    promo.current_uses += 1
                    promo.save()

                return JsonResponse(
                    {
                        "user_id": user.id,
                        "order_id": order.id,
                        "goods": response_goods,
                        "price": float(total_price),
                        "discount": str(promo.discount_percent / 100) if promo else "0",
                        "total": float(total_final_price),
                    },
                    status=201,
                )
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)

        except Exception as e:
            return JsonResponse(
                {"error": "Произошла ошибка при оформлении"}, status=500
            )
