def calculate_cart_total(cart_items, promocode, user):
    """Функция подсчета итоговой суммы"""
    is_valid, message = promocode.check_validity(user)
    if not is_valid:
        return sum(item.price for item in cart_items), message

    total = 0
    for item in cart_items:
        if promocode.is_applicable_to_product(item.product):
            discount = (item.price * promocode.discount_percent) / 100
            total += item.price - discount
        else:
            total += item.price

    return total, "Скидка применена к части товаров"
