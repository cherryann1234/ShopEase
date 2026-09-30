import io
import random

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from store.models import Category, Product

DATA = {
    "Gadgets": [
        ("Wireless Mouse", "Ergonomic 2.4GHz wireless mouse with silent clicks and a long-lasting battery.", 499, 25),
        ("Mechanical Keyboard", "Compact tenkeyless keyboard with tactile blue switches and white backlight.", 2499, 12),
        ("USB-C Hub 7-in-1", "HDMI, USB 3.0, SD card reader and 100W pass-through charging in one hub.", 1299, 4),
        ("Bluetooth Earbuds", "True wireless earbuds with charging case and up to 20 hours of playtime.", 1799, 30),
        ("Power Bank 20000mAh", "Fast-charging power bank with dual USB output and LED battery indicator.", 1499, 0),
    ],
    "Home": [
        ("Ceramic Coffee Mug", "350ml matte ceramic mug, dishwasher and microwave safe.", 249, 60),
        ("LED Desk Lamp", "Dimmable desk lamp with three colour modes and a flexible neck.", 899, 9),
        ("Scented Soy Candle", "Hand-poured soy candle with a calming lavender scent, 40-hour burn time.", 349, 3),
        ("Throw Pillow Cover", "Soft linen-blend cushion cover, 18 x 18 inches, hidden zipper.", 299, 40),
    ],
    "Fashion": [
        ("Canvas Tote Bag", "Sturdy cotton canvas tote with inner pocket, perfect for groceries or school.", 399, 35),
        ("Classic Cap", "Adjustable cotton baseball cap available in one universal size.", 329, 18),
        ("Everyday Backpack", "Water-resistant 20L backpack with padded laptop sleeve and USB charging port.", 1599, 6),
        ("Stainless Water Bottle", "750ml insulated bottle that keeps drinks cold for 24 hours.", 649, 22),
    ],
}
COLORS = ["#2563eb", "#0f766e", "#b45309", "#7c3aed", "#be123c", "#0369a1", "#4d7c0f"]


def make_image(text, color):
    """Small generated placeholder picture so the demo catalog looks complete."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        image = Image.new("RGB", (600, 450), color)
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.load_default(size=44)
        except TypeError:  # older Pillow
            font = ImageFont.load_default()
        draw.rectangle((20, 20, 580, 430), outline="white", width=4)
        draw.multiline_text((300, 225), text.replace(" ", "\n"), fill="white",
                            font=font, anchor="mm", align="center")
        buffer = io.BytesIO()
        image.save(buffer, "PNG")
        return buffer.getvalue()
    except Exception:
        return None


class Command(BaseCommand):
    help = "Load sample categories and products for ShopEase."

    def handle(self, *args, **options):
        random.seed(7)
        created = 0
        for cat_name, items in DATA.items():
            category, _ = Category.objects.get_or_create(name=cat_name, defaults={"slug": slugify(cat_name)})
            for name, description, price, stock in items:
                product, was_created = Product.objects.get_or_create(
                    name=name,
                    defaults={"category": category, "description": description,
                              "price": price, "stock": stock},
                )
                if was_created:
                    created += 1
                    png = make_image(name, random.choice(COLORS))
                    if png:
                        product.image.save(f"{slugify(name)}.png", ContentFile(png), save=True)
        self.stdout.write(self.style.SUCCESS(
            f"Seed complete: {created} new product(s), {Product.objects.count()} total."))
