"""
Правило 04: Основной текст.
Проверяет форматирование основного текста по Таблице 4.1.
Жирность и курсив допустимы для выделения — выводятся как предупреждения.
Пропускает строки внутри оглавления.
"""

from .base_rule import BaseRule, RuleResult


class MainTextRule(BaseRule):
    @property
    def rule_id(self): return "main_text"
    @property
    def name(self): return "Основной текст"
    @property
    def description(self): return "Проверка форматирования основного текста (Таблица 4.1)"

    def check(self, model):
        errors = []
        warnings = []
        main_paragraphs = [e for e in model.elements if e['text_category'] == 'main']

        if not main_paragraphs:
            return RuleResult(status='pass', summary='Основной текст не найден')

        # Границы оглавления — исключаем из проверки
        toc_start = None
        toc_end = None
        for h in model.headings:
            if h['heading_level'] == 1 and h['text'].upper() in ('ОГЛАВЛЕНИЕ', 'СОДЕРЖАНИЕ'):
                toc_start = h['index']
            elif toc_start is not None and h['heading_level'] == 1:
                toc_end = h['index']
                break

        for e in main_paragraphs:
            # Пропускаем строки внутри оглавления
            if toc_start is not None and toc_end is not None:
                if toc_start < e['index'] < toc_end:
                    continue

            text = e['text']
            pv = text[:60] + ('...' if len(text) > 60 else '')
            issues = []
            warns = []

            # Шрифт Times New Roman
            fn = e.get('font_name')
            if fn and 'times new roman' not in fn.lower():
                issues.append(f"шрифт: {fn}")

            # Размер 14 пт
            fs = e.get('font_size_pt')
            if fs is not None and abs(fs - 14) > 0.5:
                issues.append(f"размер: {fs:.0f} пт (нужен 14)")

            # Жирность и курсив — допустимы для выделения
            if e.get('bold'):
                warns.append("полужирный (допустимо для выделения)")
            if e.get('italic'):
                warns.append("курсив (допустимо для выделения)")

            # Выравнивание по ширине
            if e.get('alignment') is not None and e['alignment'] != 3:
                issues.append("выравнивание должно быть по ширине")

            # Отступ слева 0
            li = e.get('left_indent')
            if li is not None and abs(li) > 0.1:
                issues.append(f"отступ слева: {li:.1f} см (должен 0)")

            # Отступ первой строки 1.25 см
            fi = e.get('first_line_indent')
            if fi is not None and abs(fi - 1.25) > 0.25:
                issues.append(f"отступ первой строки: {fi:.2f} см (нужен 1.25)")

            # Интервал перед 0
            sb = e.get('space_before')
            if sb is not None and abs(sb) > 2:
                issues.append(f"интервал перед: {sb:.0f} пт (нужен 0)")

            # Интервал после 0
            sa = e.get('space_after')
            if sa is not None and abs(sa) > 2:
                issues.append(f"интервал после: {sa:.0f} пт (нужен 0)")

            # Междустрочный 1.5
            ls = e.get('line_spacing')
            if ls is not None and isinstance(ls, (int, float)) and abs(ls - 1.5) > 0.1:
                issues.append(f"междустрочный: {ls:.2f} (нужен 1.5)")

            if issues:
                errors.append(f"'{pv}': {', '.join(issues)}")
                if len(errors) >= 30:
                    errors.append("... показаны первые 30 абзацев с нарушениями")
                    break
            elif warns:
                warnings.append(f"'{pv}': {', '.join(warns)}")

        details = errors + warnings

        if errors:
            return RuleResult(
                status='fail', summary=f'Нарушений в основном тексте: {len(errors)}',
                details=details,
                received=f"Проверено абзацев: {len(main_paragraphs)}",
                expected="Times New Roman 14pt, по ширине, отступ 1.25 см, межстрочный 1.5, интервалы 0"
            )

        if warnings:
            return RuleResult(
                status='pass', summary=f'Основной текст в порядке (есть предупреждения)',
                details=details,
                received=f"Проверено абзацев: {len(main_paragraphs)}"
            )

        return RuleResult(
            status='pass',
            summary=f'Основной текст оформлен правильно ({len(main_paragraphs)} абзацев)',
            received=f"Проверено абзацев: {len(main_paragraphs)}"
        )