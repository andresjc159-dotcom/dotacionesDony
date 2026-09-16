"""Context processors de la tienda."""

def carrito(request):
    cart = request.session.get("carrito_web", [])
    count = sum(item.get("cantidad", 0) for item in cart)
    return {"carrito_web_count": count}
