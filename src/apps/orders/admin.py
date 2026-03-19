from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ("product",)
    readonly_fields = (
        "price_at_purchase",
        "discount_amount",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_amount", "promocode", "created_at")
    list_filter = ("created_at", "promocode")
    search_fields = ("id", "user__username", "user__email")
    inlines = [OrderItemInline]
