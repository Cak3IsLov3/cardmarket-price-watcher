from decimal import Decimal


def should_alert(
    previous_low: Decimal | None, current_low: Decimal | None, target: Decimal
) -> bool:
    if current_low is None or current_low > target:
        return False
    if previous_low is None:
        return True
    return previous_low > target