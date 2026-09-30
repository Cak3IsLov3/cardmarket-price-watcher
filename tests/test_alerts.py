from decimal import Decimal

import pytest

from app.services.alerts import should_alert

TARGET = Decimal("1.00")


@pytest.mark.parametrize(
    ("previous", "current", "expected"),
    [
        (None, Decimal("0.48"), True),  # first check, already below target
        (Decimal("1.20"), Decimal("0.90"), True),  # drops below target
        (Decimal("1.20"), Decimal("1.00"), True),  # exactly on target counts
        (Decimal("0.90"), Decimal("0.80"), False),  # was already below
        (Decimal("0.90"), Decimal("1.10"), False),  # rises above target
        (None, Decimal("1.50"), False),  # first check, above target
        (Decimal("1.20"), None, False),  # no price in the feed
    ],
)
def test_should_alert(previous, current, expected):
    assert should_alert(previous, current, TARGET) is expected