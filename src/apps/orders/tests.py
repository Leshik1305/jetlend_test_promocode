from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from src.apps.orders.models import Order
from src.apps.products.models import Category, Product
from src.apps.promocodes.models import PromoCode

User = get_user_model()


class OrderCreateTests(APITestCase):
    def setUp(self):

        self.user = User.objects.create(username="testuser")

        self.category = Category.objects.create(name="Тестовая категория")

        self.product1 = Product.objects.create(
            name="Товар 1", price=100, stock=10, category=self.category
        )
        self.product2 = Product.objects.create(
            name="Товар 2", price=200, stock=5, category=self.category
        )

        self.promo = PromoCode.objects.create(
            code="NEW",
            discount_percent=10,
            valid_until=timezone.now() + timedelta(days=30),
            max_uses=50,
        )

        self.url = reverse("order-create")

    def test_create_order_success_no_promo(self):
        """1. Успешное создание заказа БЕЗ промокода"""
        data = {
            "user_id": self.user.id,
            "goods": [{"good_id": self.product1.id, "quantity": 2}],
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["price"], 200.0)
        self.assertEqual(response.data["discount"], "0")
        self.assertEqual(response.data["total"], 200.0)
        self.assertEqual(len(response.data["goods"]), 1)

        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock, 8)

    def test_create_order_success_with_promo(self):
        """2. Успешное создание заказа С промокодом (проверка расчетов)"""
        data = {
            "user_id": self.user.id,
            "goods": [{"good_id": self.product1.id, "quantity": 2}],  # 100 * 2 = 200
            "promo_code": "NEW",  # -10% = 180
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["price"], 200.0)
        self.assertEqual(response.data["discount"], "0.1")  # 10% в формате доли
        self.assertEqual(response.data["total"], 180.0)

        good = response.data["goods"][0]
        self.assertEqual(Decimal(good["discount"]), Decimal("0.1"))
        self.assertEqual(good["total"], 180.0)

    def test_create_order_insufficient_stock(self):
        """3. Ошибка: Недостаточно товара на складе"""
        data = {
            "user_id": self.user.id,
            "goods": [
                {"good_id": self.product2.id, "quantity": 10}  # На складе всего 5
            ],
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)
