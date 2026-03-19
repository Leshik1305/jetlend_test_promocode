from django.contrib import admin

from .models import PromoCode


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_percent",
        "valid_until",
        "current_uses",
        "max_uses",
        "is_active",
    )
    list_filter = ("is_active", "valid_until", "discount_percent")
    search_fields = ("code",)
    filter_horizontal = ("categories",)
    readonly_fields = ("current_uses",)
