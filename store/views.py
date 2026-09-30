from decimal import Decimal

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q
from django.http import HttpResponse, QueryDict
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from .cart import Cart
from .forms import OrderForm, ProductForm, QuantityForm, StockForm
from .models import SHIPPING_FEES, SHIPPING_LABELS, Category, Order, OrderItem, Product

SORT_OPTIONS = [
    ("newest", "Newest"),
    ("price_asc", "Price: low to high"),
    ("price_desc", "Price: high to low"),
]
SORT_FIELDS = {"newest": "-date_created", "price_asc": "price", "price_desc": "-price"}
PAGE_SIZE = 8


# ---------------------------------------------------------------- helpers
def is_htmx(request):
    """True for HTMX requests, except history-restore requests, which need a full page."""
    return (request.headers.get("HX-Request") == "true"
            and request.headers.get("HX-History-Restore-Request") != "true")


def hx_redirect(request, url):
    if is_htmx(request):
        response = HttpResponse()
        response["HX-Redirect"] = url
        return response
    return redirect(url)


def not_found(request, message="That item could not be found."):
    """Full 404 page normally; a small inline error partial for HTMX requests."""
    if is_htmx(request):
        return render(request, "partials/_error.html", {"message": message}, status=404)
    return render(request, "404.html", status=404)


def handler404(request, exception=None):
    return not_found(request)


def messages_oob(request):
    """Empty main swap plus an out-of-band refresh of the #messages area."""
    return HttpResponse(render_to_string("partials/_messages.html", {"oob": True}, request=request))


def summary_context(cart, method="standard"):
    if method not in SHIPPING_FEES:
        method = "standard"
    lines = cart.lines()
    subtotal = cart.subtotal(lines)
    shipping = SHIPPING_FEES[method]
    return {
        "lines": lines,
        "subtotal": subtotal,
        "shipping": shipping,
        "shipping_label": SHIPPING_LABELS[method],
        "total": subtotal + shipping,
        "item_count": sum(line.quantity for line in lines),
        "notices": cart.notices,
    }


# ------------------------------------------------------- Page 1: catalog
def product_list(request):
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    sort = request.GET.get("sort", "newest")

    products = Product.objects.filter(is_active=True).select_related("category")
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if category:
        products = products.filter(category__slug=category)
    products = products.order_by(SORT_FIELDS.get(sort, "-date_created"), "-id")

    page = Paginator(products, PAGE_SIZE).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    query = params.urlencode()

    context = {
        "page": page,
        "q": q,
        "category": category,
        "sort": sort,
        "sort_options": SORT_OPTIONS,
        "categories": Category.objects.all(),
        "page_prefix": f"?{query}&" if query else "?",
    }
    if is_htmx(request):
        return render(request, "partials/_product_grid.html", context)
    return render(request, "product_list.html", context)


def product_detail(request, pk):
    product = Product.objects.filter(pk=pk, is_active=True).select_related("category").first()
    if product is None:
        return not_found(request)
    form = QuantityForm(max_qty=product.stock)
    return render(request, "product_detail.html", {"product": product, "form": form})


# ------------------------------------------------- Page 2: product management
def product_manage(request):
    q = request.GET.get("q", "").strip()
    products = Product.objects.select_related("category").order_by("-id")
    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(description__icontains=q) | Q(category__name__icontains=q))
    context = {"products": products, "q": q}
    if is_htmx(request):
        return render(request, "partials/_manage_table.html", context)
    return render(request, "product_manage.html", context)


def product_form(request, pk=None):
    product = None
    if pk is not None:
        product = Product.objects.filter(pk=pk).first()
        if product is None:
            return not_found(request, "That product no longer exists.")

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            saved = form.save()
            verb = "updated" if product else "created"
            messages.success(request, f"“{saved.name}” was {verb} successfully.")
            return hx_redirect(request, reverse("product_manage"))
    else:
        form = ProductForm(instance=product)

    context = {"form": form, "product": product}
    if is_htmx(request) and request.method == "POST":
        return render(request, "partials/_product_form.html", context)
    return render(request, "product_form.html", context)


@require_http_methods(["DELETE", "POST"])
def product_delete(request, pk):
    product = Product.objects.filter(pk=pk).first()
    if product is None:
        messages.error(request, "That product no longer exists.")
    else:
        name = product.name
        product.delete()
        messages.success(request, f"“{name}” was deleted.")
    if is_htmx(request):
        return messages_oob(request)
    return redirect("product_manage")


@require_POST
def product_toggle(request, pk):
    product = Product.objects.filter(pk=pk).select_related("category").first()
    if product is None:
        messages.error(request, "That product no longer exists.")
        return messages_oob(request)
    product.is_active = not product.is_active
    product.save(update_fields=["is_active"])
    return render(request, "partials/_manage_row.html", {"p": product})


@require_POST
def product_stock(request, pk):
    product = Product.objects.filter(pk=pk).select_related("category").first()
    if product is None:
        messages.error(request, "That product no longer exists.")
        return messages_oob(request)
    form = StockForm(request.POST)
    context = {"p": product}
    if form.is_valid():
        product.stock = form.cleaned_data["stock"]
        product.save(update_fields=["stock"])
    else:
        context["row_error"] = form.errors["stock"][0]
        context["attempted"] = request.POST.get("stock", "")
    return render(request, "partials/_manage_row.html", context)


# ------------------------------------------------------- Page 3: cart
def render_cart(request, cart, message=None, ok=True):
    context = summary_context(cart)
    context.update(message=message, ok=ok, oob=True)
    if is_htmx(request):
        return render(request, "partials/_cart_container.html", context)
    if message:
        (messages.success if ok else messages.error)(request, message)
    return redirect("cart")


def cart_view(request):
    context = summary_context(Cart(request))
    context["oob"] = False
    if is_htmx(request):
        context["oob"] = True
        return render(request, "partials/_cart_container.html", context)
    return render(request, "cart.html", context)


@require_POST
def cart_add(request, pk):
    product = Product.objects.filter(pk=pk, is_active=True).first()
    if product is None:
        return not_found(request, "This product is no longer available.")
    form = QuantityForm(request.POST)
    if form.is_valid():
        ok, message = Cart(request).add(product, form.cleaned_data["quantity"])
    else:
        ok, message = False, form.errors["quantity"][0]
    if is_htmx(request):
        return render(request, "partials/_add_result.html", {"ok": ok, "message": message, "oob": True})
    (messages.success if ok else messages.error)(request, message)
    return redirect(request.META.get("HTTP_REFERER") or reverse("product_list"))


@require_http_methods(["PUT", "POST"])
def cart_update(request, pk):
    data = QueryDict(request.body) if request.method == "PUT" else request.POST
    cart = Cart(request)
    product = Product.objects.filter(pk=pk, is_active=True).first()
    if product is None or str(pk) not in cart.data:
        cart.remove(pk)
        return render_cart(request, cart, "That item is no longer available and was removed from your cart.", False)
    form = QuantityForm(data)
    if form.is_valid():
        ok, message = cart.set_quantity(product, form.cleaned_data["quantity"])
    else:
        ok, message = False, form.errors["quantity"][0]
    return render_cart(request, cart, message, ok)


@require_http_methods(["DELETE", "POST"])
def cart_remove(request, pk):
    cart = Cart(request)
    cart.remove(pk)
    return render_cart(request, cart, "Item removed from your cart.", True)


def order_summary(request):
    """HTMX target for the shipping-method select: recompute the summary."""
    context = summary_context(Cart(request), request.GET.get("shipping_method", "standard"))
    return render(request, "partials/_cart_summary.html", context)


def place_order(form, cart):
    """Re-check stock inside a transaction, then create the Order + OrderItems,
    reduce stock and clear the cart. Returns (order, problems)."""
    problems = []
    with transaction.atomic():
        products = Product.objects.select_for_update().in_bulk([int(pid) for pid in cart.data])
        wanted = []
        for pid, qty in cart.data.items():
            product = products.get(int(pid))
            if product is None or not product.is_active:
                problems.append("An item in your cart is no longer available.")
            elif qty > product.stock:
                problems.append(
                    f"Only {product.stock} of {product.name} left in stock (you requested {qty}).")
            else:
                wanted.append((product, qty))
        if problems:
            return None, problems

        order = form.save(commit=False)
        subtotal = sum((product.price * qty for product, qty in wanted), Decimal("0.00"))
        order.total = subtotal + SHIPPING_FEES[order.shipping_method]
        order.save()
        for product, qty in wanted:
            OrderItem.objects.create(order=order, product=product, quantity=qty, unit_price=product.price)
            Product.objects.filter(pk=product.pk).update(stock=F("stock") - qty)
    cart.clear()
    return order, []


def checkout(request):
    cart = Cart(request)
    if not cart.data:
        messages.info(request, "Your cart is empty. Add something before checking out.")
        return hx_redirect(request, reverse("cart"))

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order, problems = place_order(form, cart)
            if order:
                return hx_redirect(request, reverse("order_success", args=[order.pk]))
            for problem in dict.fromkeys(problems):
                form.add_error(None, problem)
            cart.lines()  # sync the cart with what is really available
            if not cart.data:
                messages.error(request, "The items in your cart are no longer available.")
                return hx_redirect(request, reverse("cart"))
    else:
        form = OrderForm()

    method = form["shipping_method"].value() or "standard"
    context = summary_context(cart, method)
    context["form"] = form
    if is_htmx(request) and request.method == "POST":
        context["oob"] = True  # also refresh the order summary next to the form
        return render(request, "partials/_checkout_form.html", context)
    return render(request, "checkout.html", context)


def order_success(request, pk):
    order = Order.objects.filter(pk=pk).prefetch_related("items__product").first()
    if order is None:
        return not_found(request, "That order could not be found.")
    return render(request, "order_success.html", {"order": order})
