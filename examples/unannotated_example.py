"""Example showing automatic logic discovery without explicit annotations."""


def process_order(subtotal: float, tax_rate: float, user_role: str, account_balance: float):
    # Arithmetic & Business logic
    total_tax = subtotal * tax_rate
    gross_total = subtotal + total_tax

    # Relational & Security decision logic
    has_discount_privilege = user_role == "vip"

    # Conditional control & Constraint logic
    if gross_total > 500:
        shipping_fee = 0.0
    else:
        shipping_fee = 15.0

    # Validation logic
    assert account_balance >= 0, "Account balance cannot be negative"

    return gross_total + shipping_fee
