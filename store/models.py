from decimal import Decimal

from django.db import models

LOW_STOCK_THRESHOLD = 5

SHIPPING_CHOICES = [
    ("standard", "Standard (3-5 days) - ₱50"),
    ("express", "Express (1-2 days) - ₱150"),
    ("pickup", "Store pickup - Free"),
]
SHIPPING_FEES = {
    "standard": Decimal("50.00"),
    "express": Decimal("150.00"),
    "pickup": Decimal("0.00"),
}
SHIPPING_LABELS = {"standard": "Standard", "express": "Express", "pickup": "Store pickup"}

PAYMENT_CHOICES = [
    ("cod", "Cash on Delivery"),
    ("later", "Pay Later"),
]

STATUS_CHOICES = [
    ("pending", "Pending"),
    ("confirmed", "Confirmed"),
    ("shipped", "Shipped"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
]


class Category(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=120)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_created"]

    def __str__(self):
        return self.name

    # Presentation helpers live on the model so templates stay logic-free.
    @property
    def is_out_of_stock(self):
        return self.stock <= 0

    @property
    def stock_status(self):
        if self.stock <= 0:
            return "out"
        if self.stock <= LOW_STOCK_THRESHOLD:
            return "low"
        return "in"

    @property
    def stock_label(self):
        return {"in": "In Stock", "low": "Low Stock", "out": "Out of Stock"}[self.stock_status]


class Order(models.Model):
    customer_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=80, blank=True)
    shipping_method = models.CharField(max_length=20, choices=SHIPPING_CHOICES, default="standard")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default="cod")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_created"]

    def __str__(self):
        return f"Order #{self.pk} - {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="order_items")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product}"
