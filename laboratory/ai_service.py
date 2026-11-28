import os
from time import perf_counter

from google import genai
from google.genai import types
from concurrent.futures import ThreadPoolExecutor


SYSTEM_PROMPT = """
Ты врачебный помощник по интерпретации лабораторных исследований
для дневника отделения реанимации и интенсивной терапии.

Правила формирования заключения:

1. Используй профессиональную медицинскую терминологию.
2. Указывай только клинически значимые отклонения.
3. Объединяй однотипные нарушения в лабораторные синдромы.
4. При наличии нескольких дат указывай динамику:
   нарастание, снижение, сохраняется, нормализация.
5. Не перечисляй показатели в пределах нормы.
6. Не дублируй числовые значения без клинической необходимости.
7. Не объясняй причины нарушений без достаточных данных.
8. Не назначай лечение и дополнительные обследования.
9. Не устанавливай необоснованные диагнозы.
10. Указывай степень нарушения только при наличии
    достаточных данных и применимых критериев.
11. Не выдумывай отсутствующие показатели.
12. Не используй вводные фразы:
    «по результатам анализов», «следует отметить»,
    «биохимически регистрируется», «отрицательный тренд».
13. Не используй заголовки, списки и Markdown.
14. Формируй заключение одним абзацем из 1–3 предложений.
15. Стремись к объёму 20–50 слов.
16. Не опускай критически значимые отклонения ради краткости.
17. Указывай ограничения только тогда, когда они существенно
    влияют на достоверность заключения.

Возвращай только готовое медицинское заключение.
"""


# Модель искусственного интеллекта
AI_MODEL = "gemini-3.5-flash-lite"


# Формирование лабораторного заключения
def analyze_laboratory(analyses: str) -> str:
    """Интерпретация лабораторных исследований с помощью ИИ."""

    if not analyses.strip():
        raise ValueError("Отсутствуют лабораторные данные")

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("Не задан GEMINI_API_KEY")

    start = perf_counter()

    try:
        with genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=30000,
            ),
        ) as client:
            response = client.models.generate_content(
                model=AI_MODEL,
                contents=analyses,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.1,
                    max_output_tokens=512,
                ),
            )

            if not response.text:
                raise ValueError("ИИ не сформировал заключение")

            return response.text.strip()

    finally:
        elapsed = perf_counter() - start

        print(f"Модель ИИ: {AI_MODEL}")
        print(f"Время ИИ-анализа: {elapsed:.2f} сек.")


def analyze_laboratory_sections(sections: dict[str, str]) -> str:
    """Независимый параллельный анализ лабораторных категорий."""

    if not sections:
        raise ValueError("Отсутствуют лабораторные исследования")

    def analyze_section(item):
        name, text = item

        conclusion = analyze_laboratory(f"Категория исследований: {name}\n\n{text}")

        return f"{name}: {conclusion}"

    with ThreadPoolExecutor(max_workers=3) as executor:
        conclusions = list(
            executor.map(
                analyze_section,
                sections.items(),
            )
        )

    return "\n\n".join(conclusions)
