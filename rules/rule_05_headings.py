"""
Правило 05: Заголовки.
Проверяет форматирование заголовков всех уровней по Таблице 5.1.
Пропускает строки, находящиеся внутри оглавления.
"""

import re as _re
from .base_rule import BaseRule, RuleResult

# «Приложение А», «Приложение Б» и т.д. — заголовок уровня 2 с особым форматированием
_APPENDIX_H_RE = _re.compile(r'^[Пп]риложени[еяю]\s+[А-ЯA-Z]$')


class HeadingsRule(BaseRule):
    @property
    def rule_id(self): return "headings"
    @property
    def name(self): return "Заголовки"
    @property
    def description(self): return "Проверка форматирования заголовков (Таблица 5.1)"

    EXP = {
        1: {'size': 18, 'sb': 0, 'sa': 12, 'ls': 1.5, 'indent': 1.25, 'indent_main': 0, 'align': 3, 'left': 0},
        2: {'size': 16, 'sb': 24, 'sa': 12, 'ls': 1.5, 'indent': 1.25, 'align': 3, 'left': 0},
        3: {'size': 14, 'sb': 24, 'sa': 12, 'ls': 1.5, 'indent': 1.25, 'align': 3, 'left': 0},
    }

    MAIN_SECTIONS = [
        'аннотация', 'оглавление', 'содержание', 'введение', 'заключение',
        'список использованных источников', 'список используемых сокращений и обозначений',
        'приложения'
    ]

    def check(self, model):
        errors = []

        # Определяем границы оглавления
        toc_start = None
        toc_end = None
        for h in model.headings:
            if h['heading_level'] == 1 and h['text'].upper() in ('ОГЛАВЛЕНИЕ', 'СОДЕРЖАНИЕ'):
                toc_start = h['index']
            elif toc_start is not None and h['heading_level'] == 1 and h['text'].upper() not in ('ОГЛАВЛЕНИЕ', 'СОДЕРЖАНИЕ'):
                toc_end = h['index']
                break

        for h in model.headings:
            # Пропускаем заголовки внутри оглавления
            if toc_start is not None and toc_end is not None:
                if toc_start < h['index'] < toc_end:
                    continue

            lv = h['heading_level']
            if lv not in self.EXP:
                continue

            exp = self.EXP[lv]
            text = h['text']
            pv = text[:60] + ('...' if len(text) > 60 else '')
            issues = []

            is_main = any(s in text.lower() for s in self.MAIN_SECTIONS)
            is_appendix = bool(_APPENDIX_H_RE.match(text))

            # Шрифт Times New Roman
            fn = h.get('font_name')
            if fn and 'times new roman' not in fn.lower():
                issues.append(f"шрифт: {fn}")

            # Размер
            fs = h.get('font_size_pt')
            if fs is not None and abs(fs - exp['size']) > 0.5:
                issues.append(f"размер: {fs:.0f} пт (нужен {exp['size']})")

            # Полужирный
            if not h.get('bold'):
                issues.append("должен быть полужирным")

            # Курсив
            if h.get('italic'):
                issues.append("не должен быть курсивом")

            # ПРОПИСНЫЕ для основных разделов 1 уровня
            if lv == 1 and is_main:
                if not text.isupper():
                    issues.append("должен быть ПРОПИСНЫМИ буквами")

            # Выравнивание
            expected_align = 1 if (lv == 1 and is_main) or is_appendix else exp['align']
            actual_align = h.get('alignment')
            if actual_align is not None and actual_align != expected_align:
                align_names = {0: 'по левому', 1: 'по центру', 2: 'по правому', 3: 'по ширине'}
                issues.append(
                    f"выравнивание: {align_names.get(actual_align, str(actual_align))}, "
                    f"должно быть {align_names.get(expected_align, str(expected_align))}"
                )

            # Интервал перед
            exp_sb = 0 if is_appendix else exp['sb']
            sb = h.get('space_before')
            if sb is not None and abs(sb - exp_sb) > 2:
                issues.append(f"интервал перед: {sb:.0f} пт (нужен {exp_sb})")

            # Интервал после
            exp_sa = 0 if is_appendix else exp['sa']
            sa = h.get('space_after')
            if sa is not None and abs(sa - exp_sa) > 2:
                issues.append(f"интервал после: {sa:.0f} пт (нужен {exp_sa})")

            # Междустрочный
            ls = h.get('line_spacing')
            if ls is not None and isinstance(ls, (int, float)) and abs(ls - exp['ls']) > 0.1:
                issues.append(f"междустрочный: {ls:.2f} (нужен {exp['ls']})")

            # Отступ первой строки
            expected_indent = (exp.get('indent_main', 0) if (lv == 1 and is_main)
                               else 0 if is_appendix
                               else exp['indent'])
            fi = h.get('first_line_indent')
            if fi is not None and abs(fi - expected_indent) > 0.25:
                issues.append(f"отступ первой строки: {fi:.2f} см (нужен {expected_indent})")

            # Отступ слева
            li = h.get('left_indent')
            if li is not None and abs(li - exp['left']) > 0.1:
                issues.append(f"отступ слева: {li:.1f} см (должен {exp['left']})")

            # Точка в конце
            if text.endswith('.'):
                issues.append("в конце заголовка не должно быть точки")

            if issues:
                errors.append(f"'{pv}' (уровень {lv}): {', '.join(issues)}")

        if errors:
            return RuleResult(
                status='fail', summary=f'Нарушений в заголовках: {len(errors)}',
                details=errors,
                received=f"Проверено заголовков: {len(model.headings)}",
                expected="Times New Roman, полужирный, 18/16/14 пт, интервалы по табл. 5.1, основные разделы ПРОПИСНЫМИ по центру без отступа"
            )

        return RuleResult(
            status='pass',
            summary=f'Все {len(model.headings)} заголовков оформлены правильно',
            received=f"Проверено заголовков: {len(model.headings)}"
        )