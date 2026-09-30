import re

from django import forms
from django.urls import reverse_lazy

from .models import Order, Product

PH_MOBILE = re.compile(r"^(09\d{9}|\+639\d{9})$")


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "description", "price", "stock", "image", "is_active"]
        labels = {
            "name": "Product name",
            "price": "Price (₱)",
            "stock": "Stock quantity",
            "image": "Product image",
            "is_active": "Active (visible in the catalog)",
        }
        help_texts = {
            "name": "At least 3 characters. Must be unique.",
            "price": "Must be greater than 0.",
            "stock": "Whole number, 0 or higher.",
            "image": "Optional. JPG or PNG.",
            "is_active": "Untick to hide this product from customers.",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Wireless Mouse"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Short product description"}),
            "price": forms.NumberInput(attrs={"step": "0.01", "min": "0.01", "placeholder": "0.00"}),
            "stock": forms.NumberInput(attrs={"min": "0"}),
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if len(name) < 3:
            raise forms.ValidationError("Product name must be at least 3 characters.")
        duplicate = Product.objects.filter(name__iexact=name).exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError("A product with this name already exists.")
        return name

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Price must be greater than 0.")
        return price

    def clean_stock(self):
        stock = self.cleaned_data["stock"]
        if stock < 0:
            raise forms.ValidationError("Stock cannot be negative.")
        return stock


class StockForm(forms.Form):
    stock = forms.IntegerField(error_messages={"invalid": "Enter a whole number."})

    def clean_stock(self):
        stock = self.cleaned_data["stock"]
        if stock < 0:
            raise forms.ValidationError("Stock cannot be negative.")
        return stock


class QuantityForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Quantity",
        error_messages={
            "invalid": "Enter a whole number.",
            "min_value": "Quantity must be at least 1.",
            "required": "Enter a quantity.",
        },
        widget=forms.NumberInput(attrs={"class": "qty", "min": "1"}),
    )

    def __init__(self, *args, max_qty=None, **kwargs):
        super().__init__(*args, **kwargs)
        if max_qty is not None:
            self.fields["quantity"].widget.attrs["max"] = max_qty


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["customer_name", "email", "phone", "address", "city",
                  "shipping_method", "payment_method"]
        labels = {
            "customer_name": "Full name",
            "email": "Email address",
            "phone": "Mobile number",
            "address": "Street address",
            "city": "City",
            "shipping_method": "Shipping method",
            "payment_method": "Payment method",
        }
        help_texts = {
            "customer_name": "First and last name.",
            "phone": "Format: 09XXXXXXXXX or +639XXXXXXXXX.",
            "address": "Required for Standard and Express delivery.",
            "city": "Required for Standard and Express delivery.",
            "payment_method": "Payment is simulated - no real charge is made.",
        }
        widgets = {
            "customer_name": forms.TextInput(attrs={"placeholder": "Juan Dela Cruz", "autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"placeholder": "juan@example.com"}),
            "phone": forms.TextInput(attrs={"placeholder": "09171234567", "inputmode": "tel"}),
            "address": forms.Textarea(attrs={"rows": 3, "placeholder": "House no., street, barangay"}),
            "city": forms.TextInput(attrs={"placeholder": "Angeles City"}),
            # Changing the shipping method asks the server to redraw the order summary.
            "shipping_method": forms.Select(attrs={
                "hx-get": reverse_lazy("order_summary"),
                "hx-trigger": "change",
                "hx-target": "#order-summary",
                "hx-swap": "outerHTML",
            }),
            "payment_method": forms.RadioSelect(),
        }

    def clean_customer_name(self):
        name = " ".join(self.cleaned_data["customer_name"].split())
        if len(name.split()) < 2:
            raise forms.ValidationError("Please enter your full name (first and last name).")
        return name

    def clean_email(self):
        return self.cleaned_data["email"].lower()

    def clean_phone(self):
        phone = re.sub(r"[\s-]", "", self.cleaned_data["phone"])
        if not PH_MOBILE.match(phone):
            raise forms.ValidationError(
                "Enter a valid Philippine mobile number: 09XXXXXXXXX or +639XXXXXXXXX.")
        return phone

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("shipping_method")
        address = (cleaned.get("address") or "").strip()
        city = (cleaned.get("city") or "").strip()
        if method in ("standard", "express"):
            problems = []
            if not address:
                problems.append(("address", "Street address is required for delivery."))
            elif method == "express" and len(address) < 10:
                problems.append(("address", "Express shipping needs a complete street address (10+ characters)."))
            if not city:
                problems.append(("city", "City is required for delivery."))
            if problems:
                if method == "express":
                    self.add_error(None, "Express shipping requires a complete address and city.")
                for field, message in problems:
                    self.add_error(field, message)
        return cleaned
