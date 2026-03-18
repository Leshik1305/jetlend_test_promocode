from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

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

        try:
            order = OrderService.create_order(
                user=user,
                goods_data=input_serializer.validated_data["goods"],
                promocode=input_serializer.validated_data.get("promo_code"),
            )

            output_serializer = OrderOutputSerializer(order)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
