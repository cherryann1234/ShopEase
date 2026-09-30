from django.contrib import admin

from .models import Category, Order, OrderItem, Product

admin.site.register(Category)
admin.site.register(Product)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "total", "status", "date_created")
    inlines = [OrderItemInline]
