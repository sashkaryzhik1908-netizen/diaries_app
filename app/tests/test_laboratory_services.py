import pytest

from laboratory.services import format_indicator_value, generate_laboratory_text


@pytest.mark.parametrize(
    ("value", "precision", "expected"),
    [
        ("74.26", 1, "74.3"),
        ("74.24", 1, "74.2"),
        ("74.25", 1, "74.3"),
        ("74,26", 1, "74,3"),
        ("74,25", 1, "74,3"),
        ("74.256", 2, "74.26"),
        ("74", 1, "74.0"),
        ("74.2", 0, "74"),
        ("-74.25", 1, "-74.3"),
    ],
)
def test_format_indicator_value_rounding(value, precision, expected):
    assert format_indicator_value(value, precision) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("> 5.256", "> 5.3"),
        ("< 5,256", "< 5,3"),
        ("≤ 5.256", "≤ 5.3"),
        ("≥ 5,256", "≥ 5,3"),
        ("  >5.256", "  >5.3"),
    ],
)
def test_format_indicator_value_preserves_prefix(
    value,
    expected,
):
    assert format_indicator_value(value, 1) == expected


@pytest.mark.parametrize(
    "value",
    [
        "не определено",
        "abc",
        "",
        "—",
        "5,2%",
    ],
)
def test_format_indicator_value_returns_unrecognized_value_unchanged(value):
    assert format_indicator_value(value, 1) == value


def test_format_indicator_value_without_precision():
    value = "74.256"

    assert format_indicator_value(value, None) == value


def test_format_indicator_value_preserves_suffix():
    value = "74.256 мг/л"

    assert format_indicator_value(value, 1) == "74.3 мг/л"


from app.extensions import db
from laboratory.models import (
    LaboratoryCategory,
    LaboratoryIndicator,
)
from laboratory.services import format_laboratory_results


def create_laboratory_indicator(
    category,
    name,
    code,
    unit=None,
    precision=None,
):
    indicator = LaboratoryIndicator(
        category_id=category.id,
        name=name,
        code=code,
        unit=unit,
        precision=precision,
    )

    db.session.add(indicator)
    db.session.flush()

    return indicator


def test_format_laboratory_results_groups_indicators(app):
    with app.app_context():
        category = LaboratoryCategory(
            name="Биохимия",
            slug="biochemistry",
        )
        db.session.add(category)
        db.session.flush()

        indicator = create_laboratory_indicator(
            category,
            "АЛТ",
            "ALT",
            "Ед/л",
        )

        results = [
            {
                "datetime": "16.11.2026 12:52",
                "category": "biochemistry",
                "indicator_id": indicator.id,
                "indicator": "АЛТ",
                "code": "ALT",
                "value": "27",
                "unit": "Ед/л",
            },
        ]

        result = format_laboratory_results(results)

        assert result == ("Б/х крови:\nАЛТ — 27 Ед/л;")


def test_format_laboratory_results_rounds_values(app):
    with app.app_context():
        category = LaboratoryCategory(
            name="Биохимия",
            slug="biochemistry",
        )
        db.session.add(category)
        db.session.flush()

        indicator = create_laboratory_indicator(
            category,
            "Общий белок",
            "TP",
            "г/л",
            precision=1,
        )

        results = [
            {
                "datetime": "16.11.2026 12:52",
                "category": "biochemistry",
                "indicator_id": indicator.id,
                "indicator": "Общий белок",
                "code": "TP",
                "value": "74.26",
                "unit": "г/л",
            },
        ]

        result = format_laboratory_results(results)

        assert "Общий белок — 74.3 г/л;" in result


def test_format_laboratory_results_combines_values(app):
    with app.app_context():
        category = LaboratoryCategory(
            name="Биохимия",
            slug="biochemistry",
        )
        db.session.add(category)
        db.session.flush()

        indicator = create_laboratory_indicator(
            category,
            "АЛТ",
            "ALT",
            "Ед/л",
        )

        results = [
            {
                "datetime": "16.11.2026 12:52",
                "category": "biochemistry",
                "indicator_id": indicator.id,
                "indicator": "АЛТ",
                "code": "ALT",
                "value": "27",
            },
            {
                "datetime": "17.11.2026 12:52",
                "category": "biochemistry",
                "indicator_id": indicator.id,
                "indicator": "АЛТ",
                "code": "ALT",
                "value": "20",
            },
        ]

        result = format_laboratory_results(results)

        assert "АЛТ — 27-20 Ед/л;" in result


def test_format_laboratory_results_sorts_by_date(app):
    with app.app_context():
        category = LaboratoryCategory(
            name="Биохимия",
            slug="biochemistry",
        )
        db.session.add(category)
        db.session.flush()

        indicator = create_laboratory_indicator(
            category,
            "АЛТ",
            "ALT",
            "Ед/л",
        )

        results = [
            {
                "datetime": "17.11.2026 12:52",
                "category": "biochemistry",
                "indicator_id": indicator.id,
                "indicator": "АЛТ",
                "code": "ALT",
                "value": "20",
            },
            {
                "datetime": "16.11.2026 12:52",
                "category": "biochemistry",
                "indicator_id": indicator.id,
                "indicator": "АЛТ",
                "code": "ALT",
                "value": "27",
            },
        ]

        result = format_laboratory_results(results)

        assert "АЛТ — 27-20 Ед/л;" in result


def test_format_laboratory_results_empty_results(app):
    with app.app_context():
        assert format_laboratory_results([]) == ""


def test_format_laboratory_results_handles_unknown_indicator(app):
    with app.app_context():
        results = [
            {
                "datetime": "16.11.2026 12:52",
                "category": "biochemistry",
                "indicator_id": 9999,
                "indicator": "Неизвестный показатель",
                "code": "UNKNOWN",
                "value": "10.5",
            },
        ]

        result = format_laboratory_results(results)

        assert result == ("Б/х крови:\nНеизвестный показатель — 10.5;")


def test_format_laboratory_results_sorts_indicators_by_order(app):
    with app.app_context():
        category = LaboratoryCategory(
            name="Биохимия",
            slug="biochemistry",
        )
        db.session.add(category)
        db.session.flush()

        alt = create_laboratory_indicator(category, "АЛТ", "ALT", "Ед/л")
        protein = create_laboratory_indicator(category, "Общий белок", "TP", "г/л")
        albumin = create_laboratory_indicator(category, "Альбумин", "ALB", "г/л")

        results = [
            {
                "datetime": "16.11.2026 12:52",
                "category": "biochemistry",
                "indicator_id": alt.id,
                "indicator": "АЛТ",
                "code": "ALT",
                "value": "27",
            },
            {
                "datetime": "16.11.2026 12:52",
                "category": "biochemistry",
                "indicator_id": protein.id,
                "indicator": "Общий белок",
                "code": "TP",
                "value": "74",
            },
            {
                "datetime": "16.11.2026 12:52",
                "category": "biochemistry",
                "indicator_id": albumin.id,
                "indicator": "Альбумин",
                "code": "ALB",
                "value": "35",
            },
        ]

        result = format_laboratory_results(results)

        assert result.index("Общий белок") < result.index("Альбумин")
        assert result.index("Альбумин") < result.index("АЛТ")


def test_format_laboratory_results_separates_manual_diff(app):
    with app.app_context():
        category = LaboratoryCategory(
            name="ОАК",
            slug="cbc",
        )
        db.session.add(category)
        db.session.flush()

        wbc = create_laboratory_indicator(category, "Лейкоциты", "WBC", "10^9/л")
        lymphocytes = create_laboratory_indicator(category, "Лимфоциты", "LYM", "%")

        results = [
            {
                "datetime": "16.11.2026 12:52",
                "category": "cbc",
                "indicator_id": wbc.id,
                "indicator": "Лейкоциты",
                "code": "WBC",
                "value": "10",
            },
            {
                "datetime": "16.11.2026 12:52",
                "category": "cbc",
                "indicator_id": lymphocytes.id,
                "indicator": "Лимфоциты",
                "code": "LYM",
                "value": "20",
            },
        ]

        result = format_laboratory_results(results)

        assert "ОАК:\nЛейкоциты — 10 10^9/л;" in result
        assert "Подсчет лейкоформулы:\nЛимфоциты — 20 %;" in result


def test_format_laboratory_results_uses_section_order(app):
    with app.app_context():
        cbc = LaboratoryCategory(
            name="ОАК",
            slug="cbc",
        )
        biochemistry = LaboratoryCategory(
            name="Биохимия",
            slug="biochemistry",
        )
        db.session.add_all([cbc, biochemistry])
        db.session.flush()

        wbc = create_laboratory_indicator(cbc, "Лейкоциты", "WBC", "10^9/л")
        alt = create_laboratory_indicator(biochemistry, "АЛТ", "ALT", "Ед/л")

        results = [
            {
                "datetime": "16.11.2026 12:52",
                "category": "biochemistry",
                "indicator_id": alt.id,
                "indicator": "АЛТ",
                "code": "ALT",
                "value": "27",
            },
            {
                "datetime": "16.11.2026 12:52",
                "category": "cbc",
                "indicator_id": wbc.id,
                "indicator": "Лейкоциты",
                "code": "WBC",
                "value": "10",
            },
        ]

        result = format_laboratory_results(results)

        assert result.index("ОАК:") < result.index("Б/х крови:")


def test_format_laboratory_results_without_unit(app):
    with app.app_context():
        category = LaboratoryCategory(
            name="Биохимия",
            slug="biochemistry",
        )
        db.session.add(category)
        db.session.flush()

        indicator = create_laboratory_indicator(
            category,
            "АЛТ",
            "ALT",
            unit=None,
        )

        results = [
            {
                "datetime": "16.11.2026 12:52",
                "category": "biochemistry",
                "indicator_id": indicator.id,
                "indicator": "АЛТ",
                "code": "ALT",
                "value": "27",
            },
        ]

        result = format_laboratory_results(results)

        assert result == "Б/х крови:\nАЛТ — 27;"


def test_generate_laboratory_text_full_cycle(app):
    with app.app_context():
        category = LaboratoryCategory(
            name="Биохимия",
            slug="biochemistry",
        )
        db.session.add(category)
        db.session.flush()

        create_laboratory_indicator(
            category,
            name="Общий белок",
            code="TP",
            unit="г/л",
            precision=1,
        )

        create_laboratory_indicator(
            category,
            name="Альбумин",
            code="ALB",
            unit="г/л",
            precision=1,
        )

        source_text = (
            "Дата завершения заказа: 16.11.2026 12:52\n"
            "Общий белок - 74,26 г/л;\n"
            "Альбумин - 23,35 г/л;"
        )

        result = generate_laboratory_text(source_text)

        assert "Б/х крови:" in result
        assert "Общий белок — 74,3 г/л;" in result
        assert "Альбумин — 23,4 г/л;" in result

        assert result.index("Общий белок") < result.index("Альбумин")
