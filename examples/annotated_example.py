"""Example showing explicit (L) annotations in NESR Logic."""


def calculate_discount(price: float, discount_rate: float) -> float:
    # (L)
    return price * (1.0 - discount_rate)


def check_permissions(role: str, is_active: bool) -> bool:
    # Inline (L) annotation identifying security decision logic
    can_access = (role == "admin" or role == "moderator") and is_active  # (L)
    return can_access
