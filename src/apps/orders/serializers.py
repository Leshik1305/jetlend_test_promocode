from rest_framework import serializers

from src.apps.orders.models import Order, OrderItem
from src.apps.products.models import Product


class OrderItemInputSerializer(serializers.Serializer):
    """Сериализатор для валидации входящих данных для товара."""

    good_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source="product",
    )
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    """Сериализатор для валидации входящих данных при создании заказа."""

    user_id = serializers.IntegerField()
    promo_code = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    goods = OrderItemInputSerializer(many=True)

    def validate_products(self, value):
        """Проверяет, что список товаров не пуст."""
        if not value:
            raise serializers.ValidationError("Список товаров не может быть пустым")
        return value


class OrderItemOutputSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения отдельной позиции в заказе."""

    good_id = serializers.IntegerField(source="product.id")
    price = serializers.FloatField(source="price_at_purchase")
    discount = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["good_id", "quantity", "price", "discount", "total"]

    def get_discount(self, obj):
        """Рассчитывает процент скидки для позиции заказа."""
        if obj.price_at_purchase > 0 and obj.discount_amount > 0:
            percent = obj.discount_amount / obj.price_at_purchase
            return "{:.2f}".format(percent)
        return "0.00"

    def get_total(self, obj):
        """Рассчитывает общую стоимость позиции с учетом скидки."""
        return float((obj.price_at_purchase - obj.discount_amount) * obj.quantity)


class OrderOutputSerializer(serializers.ModelSerializer):
    """Сериализатор для полного отображения информации о заказе."""

    order_id = serializers.IntegerField(source="id")
    goods = OrderItemOutputSerializer(many=True, source="items")
    price = serializers.FloatField(source="total_price_before_discount")
    discount = serializers.SerializerMethodField()
    total = serializers.FloatField(source="total_amount")

    class Meta:
        model = Order
        fields = ["user_id", "order_id", "goods", "price", "discount", "total"]

    def get_discount(self, obj):
        """Возвращает процент скидки примененного промокода."""
        price_before = obj.total_price_before_discount or 0
        price_after = obj.total_amount or 0

        if price_before <= price_after:
            return "0.00"

        if obj.promocode:
            return "{:.2f}".format(obj.promocode.discount_percent / 100)

        return "0.00"
