from rest_framework import serializers

from src.apps.orders.models import Order, OrderItem


class OrderItemInputSerializer(serializers.Serializer):
    """Сериализатор для валидации входящих данных для товара."""

    good_id = serializers.IntegerField()
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
        if obj.price_at_purchase > 0:
            return str(round(obj.discount_amount / obj.price_at_purchase, 2))
        return "0"

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
        if obj.promocode:
            return str(obj.promocode.discount_percent / 100)
        return "0"
