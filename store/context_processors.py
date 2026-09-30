def cart_count(request):
    """Item count for the navbar badge (available in every template)."""
    cart = request.session.get("cart", {})
    return {"cart_count": sum(cart.values())}
