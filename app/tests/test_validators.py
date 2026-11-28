import pytest

from app.services.validators import is_valid_dose


# Проверка корректных дозировок
@pytest.mark.parametrize(
    "dose",
    [
        "100",
        "1",
        "0.5",
        "0,5",
        "0.001",
        "100.25",
        " 100 ",
    ],
)
def test_valid_dose(dose):
    assert is_valid_dose(dose) is True


# Проверка некорректных дозировок
@pytest.mark.parametrize(
    "dose",
    [
        "",
        " ",
        "0",
        "0.0",
        "-100",
        "-0.5",
        "abc",
        "100 мг",
        "100-200",
        "1/2",
        "NaN",
        "Infinity",
        "1e3",
    ],
)
def test_invalid_dose(dose):
    assert is_valid_dose(dose) is False
