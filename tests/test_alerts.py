from decimal import Decimal

import pytest

from app.services.alerts import should_alert

TARGET = Decimal("1.00")


@pytest.mark.parametrize(
    ("previous", "current", "expected"),
    [
        pytest.param(None, Decimal("0.48"), True, id="first check, already below target"),
        pytest.param(Decimal("1.20"), Decimal("0.90"), True, id="drops below target"),
        pytest.param(Decimal("1.20"), Decimal("1.00"), True, id="exactly on target counts"),
        pytest.param(Decimal("0.90"), Decimal("0.80"), False, id="was already below"),
        pytest.param(Decimal("0.90"), Decimal("1.10"), False, id="rises above target"),
        pytest.param(None, Decimal("1.50"), False, id="first check, above target"),
        pytest.param(Decimal("1.20"), None, False, id="no price in the feed"),
    ],
)
def test_should_alert(previous, current, expected):
    assert should_alert(previous, current, TARGET) is expected
