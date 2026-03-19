from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import OrderCreateSerializer, OrderOutputSerializer
from .services import OrderService

User = get_user_model()


class OrderCreateAPIView(APIView):
    """API endpoint для создания заказов"""

    def post(self, request):
        input_serializer = OrderCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        data = input_serializer.validated_data
        user = get_object_or_404(User, id=data["user_id"])

        service = OrderService(user=user)

        order = service.create_order(
            goods_data=data["goods"],
            promocode=data.get("promo_code"),
        )

        output_serializer = OrderOutputSerializer(order)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
