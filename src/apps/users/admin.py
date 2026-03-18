from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class MyUserAdmin(UserAdmin):
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {"fields": ("email", "phone_number")}),
    )

    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("phone_number",)}),)


admin.site.register(User, UserAdmin)
