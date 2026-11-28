from app.extensions import db
from laboratory.models import (
    LaboratoryAlias,
    LaboratoryCategory,
    LaboratoryIndicator,
)
from laboratory.parser import (
    find_indicator,
    normalize_text,
    parse_indicator,
    parse_laboratory_text,
    parse_value,
)


def create_indicator(category, name, code, aliases=None, unit=None):
    indicator = LaboratoryIndicator(
        category_id=category.id,
        name=name,
        code=code,
        unit=unit,
    )
    db.session.add(indicator)
    db.session.flush()

    for alias in aliases or []:
        db.session.add(
            LaboratoryAlias(
                indicator_id=indicator.id,
                alias=alias,
            )
        )

    db.session.flush()
    return indicator


# Нормализация текста


def test_normalize_text():
    assert normalize_text("  ЭРИТРОЦИТЫ   в Ёмкости ") == "эритроциты в емкости"


# Разбор значений


def test_parse_value_with_decimal_comma_and_unit():
    result = parse_value("> 5,25 мг/л")

    assert result == {
        "value": "> 5,25",
        "unit": "мг/л",
    }


def test_parse_value_without_unit():
    result = parse_value("-1.5")

    assert result == {
        "value": "-1.5",
        "unit": "",
    }


# Поиск показателей


def test_find_indicator_by_alias(app):
    with app.app_context():
        category = LaboratoryCategory(
            name="Биохимия",
            slug="biochemistry",
        )
        db.session.add(category)
        db.session.flush()

        indicator = create_indicator(
            category,
            name="Прокальцитонин",
            code="PCT",
            aliases=[
                "Procalcitonin",
                "прокальцитонина в крови",
            ],
        )

        found, matched_name = find_indicator(
            "уровень прокальцитонина в крови",
            [indicator],
        )

        assert found is indicator
        assert matched_name == "прокальцитонина в крови"


def test_find_indicator_prefers_longest_alias(app):
    with app.app_context():
        category = LaboratoryCategory(
            name="Биохимия",
            slug="biochemistry",
        )
        db.session.add(category)
        db.session.flush()

        short = create_indicator(
            category,
            name="Билирубин",
            code="BIL",
            aliases=["билирубин"],
        )

        long = create_indicator(
            category,
            name="Общий билирубин",
            code="TBIL",
            aliases=["общий билирубин"],
        )

        found, _ = find_indicator(
            "общий билирубин в крови",
            [short, long],
        )

        assert found is long


# Разбор отдельных показателей


def test_parse_indicator_skips_urine_results(app):
    with app.app_context():
        category = LaboratoryCategory(
            name="Биохимия",
            slug="biochemistry",
        )
        db.session.add(category)
        db.session.flush()

        indicator = create_indicator(
            category,
            name="Белок",
            code="PRO",
            aliases=["белок"],
        )

        result = parse_indicator(
            raw_text="Белок в моче - 0,3 г/л",
            indicators=[indicator],
            datetime="16.11.2026 12:52",
        )

        assert result is None


def test_parse_indicator_skips_manual_diff_code_alias(app):
    with app.app_context():
        category = LaboratoryCategory(
            name="ОАК",
            slug="cbc",
        )
        db.session.add(category)
        db.session.flush()

        indicator = create_indicator(
            category,
            name="Лимфоциты",
            code="LYM",
            aliases=["LYM", "лимфоциты"],
        )

        result = parse_indicator(
            raw_text="LYM - 20 %",
            indicators=[indicator],
            datetime="16.11.2026 12:52",
        )

        assert result is None


# Обработка исходного текста


def test_parse_laboratory_text_parses_results_and_removes_duplicates(app):
    with app.app_context():
        category = LaboratoryCategory(
            name="Биохимия",
            slug="biochemistry",
        )
        db.session.add(category)
        db.session.flush()

        indicator = create_indicator(
            category,
            name="Прокальцитонин",
            code="PCT",
            aliases=["Procalcitonin"],
            unit="нг/мл",
        )

        source_text = (
            "Дата завершения заказа: 16.11.2026 12:52\n"
            "Procalcitonin - 0,5 нг/мл;\n"
            "Procalcitonin - 0.5 нг/мл;"
        )

        results = parse_laboratory_text(source_text)

        assert len(results) == 1

        assert results[0] == {
            "datetime": "16.11.2026 12:52",
            "category": "biochemistry",
            "indicator_id": indicator.id,
            "indicator": "Прокальцитонин",
            "code": "PCT",
            "raw_name": "Procalcitonin",
            "value": "0,5",
            "unit": "нг/мл",
        }


def test_parse_laboratory_text_handles_multiple_dates(app):
    with app.app_context():
        category = LaboratoryCategory(
            name="Биохимия",
            slug="biochemistry",
        )
        db.session.add(category)
        db.session.flush()

        create_indicator(
            category,
            name="Прокальцитонин",
            code="PCT",
            aliases=["Procalcitonin"],
        )

        source_text = (
            "Дата завершения заказа: 16.11.2026 12:52\n"
            "Procalcitonin - 0,5 нг/мл;\n"
            "Дата завершения заказа: 17.11.2026 09:30\n"
            "Procalcitonin - 0,8 нг/мл;"
        )

        results = parse_laboratory_text(source_text)

        assert [result["datetime"] for result in results] == [
            "16.11.2026 12:52",
            "17.11.2026 09:30",
        ]

        assert [result["value"] for result in results] == [
            "0,5",
            "0,8",
        ]


def test_parse_indicator_accepts_manual_diff_by_name(app):
    with app.app_context():
        category = LaboratoryCategory(
            name="ОАК",
            slug="cbc",
        )
        db.session.add(category)
        db.session.flush()

        indicator = create_indicator(
            category,
            name="Лимфоциты",
            code="LYM",
            aliases=[
                "LYM",
                "лимфоциты",
                "лимфоцитов",
            ],
        )

        result = parse_indicator(
            raw_text="Относительное количество лимфоцитов - 20 %",
            indicators=[indicator],
            datetime="16.11.2026 12:52",
        )

        assert result is not None
        assert result["indicator"] == "Лимфоциты"
        assert result["code"] == "LYM"
        assert result["value"] == "20"
        assert result["unit"] == "%"
