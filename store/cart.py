from dataclasses import dataclass
from decimal import Decimal

from .models import Product


@dataclass
class Line:
    product: Product
    quantity: int

    @property
    def subtotal(self):
        return self.product.price * self.quantity


class Cart:
    """Session-backed cart: session["cart"] = {"<product_id>": quantity}."""

    KEY = "cart"

    def __init__(self, request):
        self.session = request.session
        self.data = self.session.setdefault(self.KEY, {})
        self.notices = []

    def _save(self):
        self.session.modified = True

    def lines(self):
        """Return valid lines. Stale (deleted/inactive/out-of-stock) items are removed
        and over-stock quantities are reduced, each with a friendly notice."""
        products = Product.objects.in_bulk([int(pid) for pid in self.data])
        lines = []
        for pid, qty in list(self.data.items()):
            product = products.get(int(pid))
            if product is None or not product.is_active or product.stock <= 0:
                del self.data[pid]
                name = product.name if product else "An item"
                self.notices.append(f"{name} is no longer available and was removed from your cart.")
                continue
            if qty > product.stock:
                self.data[pid] = qty = product.stock
                self.notices.append(f"Only {product.stock} of {product.name} left - quantity adjusted.")
            lines.append(Line(product, qty))
        self._save()
        return lines

    @staticmethod
    def subtotal(lines):
        return sum((line.subtotal for line in lines), Decimal("0.00"))

    def add(self, product, qty):
        current = self.data.get(str(product.pk), 0)
        if product.stock <= 0:
            return False, f"{product.name} is out of stock."
        if current + qty > product.stock:
            return False, (f"Only {product.stock} in stock"
                           f" ({current} already in your cart). Please lower the quantity.")
        self.data[str(product.pk)] = current + qty
        self._save()
        return True, f"Added {qty} x {product.name} to your cart."

    def set_quantity(self, product, qty):
        if qty > product.stock:
            return False, f"Only {product.stock} of {product.name} in stock."
        self.data[str(product.pk)] = qty
        self._save()
        return True, "Cart updated."

    def remove(self, pk):
        self.data.pop(str(pk), None)
        self._save()

    def clear(self):
        self.data.clear()
        self._save()
