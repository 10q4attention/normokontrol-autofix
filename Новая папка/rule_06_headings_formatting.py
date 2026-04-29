import re
from .base_rule import BaseRule, RuleResult

class HeadingsFormattingRule(BaseRule):
    @property
    def rule_id(self): return "headings_formatting"
    @property
    def name(self): return "Оформление заголовков"
    @property
    def description(self): return "Проверка шрифта, размера, начертания, интервалов и положения"

    EXP = {
        1: {'size': 18, 'bold': True, 'all_caps': True, 'sb': 0, 'sa': 12, 'ls': 1.5,
            'indent': 1.25, 'align': 3, 'left': 0, 'right': 0},
        2: {'size': 16, 'bold': True, 'all_caps': False, 'sb': 24, 'sa': 12, 'ls': 1.5,
            'indent': 1.25, 'align': 3, 'left': 0, 'right': 0},
        3: {'size': 14, 'bold': True, 'all_caps': False, 'sb': 24, 'sa': 12, 'ls': 1.5,
            'indent': 1.25, 'align': 3, 'left': 0, 'right': 0},
    }

    MAIN_SECTIONS = [
        'аннотация', 'оглавление', 'содержание', 'введение', 'заключение',
        'список использованных источников', 'список используемых сокращений и обозначений',
        'приложения'
    ]

    def check(self, model):
        errors = []

        for h in model.headings:
            lv = h['level']
            text = h['text']
            exp = self.EXP[lv]
            issues = []

            # Определяем, основной ли это раздел (для выравнивания по центру)
            is_main = any(s in text.lower() for s in self.MAIN_SECTIONS)

            # ── Шрифт ────────────────────────────────────────────
            fn = h.get('font_name')
            if fn and 'times new roman' not in fn.lower():
                issues.append(f"шрифт: {fn} (нужен Times New Roman)")

            # ── Размер ───────────────────────────────────────────
            fs = h.get('font_size_pt')
            if fs is not None:
                if abs(fs - exp['size']) > 0.5:
                    issues.append(f"размер: {fs:.0f} пт (нужен {exp['size']} пт)")
            else:
                issues.append(f"не удалось определить размер шрифта")

            # ── Полужирный ───────────────────────────────────────
            if not h.get('bold'):
                issues.append("должен быть полужирным")

            # ── Курсив (не должно быть) ──────────────────────────
            if h.get('italic'):
                issues.append("не должен быть курсивом")

            # ── Все прописные для 1 уровня основных разделов ─────
            if lv == 1 and is_main:
                if not text.isupper():
                    issues.append("должен быть написан ПРОПИСНЫМИ буквами")

            # ── Выравнивание ─────────────────────────────────────
            expected_align = 1 if (lv == 1 and is_main) else exp['align']  # центр для основных
            actual_align = h.get('alignment')
            if actual_align is not None and actual_align != expected_align:
                align_names = {0: 'по левому краю', 1: 'по центру', 2: 'по правому краю', 3: 'по ширине'}
                issues.append(f"выравнивание: {align_names.get(actual_align, str(actual_align))}, "
                              f"должно быть {align_names.get(expected_align, str(expected_align))}")

            # ── Интервал перед ───────────────────────────────────
            sb = h.get('space_before')
            if sb is not None:
                if abs(sb - exp['sb']) > 2:
                    issues.append(f"интервал перед: {sb:.0f} пт (нужен {exp['sb']} пт)")

            # ── Интервал после ───────────────────────────────────
            sa = h.get('space_after')
            if sa is not None:
                if abs(sa - exp['sa']) > 2:
                    issues.append(f"интервал после: {sa:.0f} пт (нужен {exp['sa']} пт)")

            # ── Междустрочный ────────────────────────────────────
            ls = h.get('line_spacing')
            if ls is not None:
                if isinstance(ls, float):
                    if abs(ls - exp['ls']) > 0.1:
                        issues.append(f"междустрочный: {ls:.2f} (нужен {exp['ls']})")
                elif isinstance(ls, str) and ls.startswith('fixed'):
                    issues.append(f"междустрочный: фиксированный (нужен {exp['ls']})")

            # ── Отступ первой строки ─────────────────────────────
            indent = h.get('first_line_indent')
            if indent is not None:
                if abs(indent - exp['indent']) > 0.25:
                    issues.append(f"отступ первой строки: {indent:.2f} см (нужен {exp['indent']} см)")
            else:
                issues.append("не удалось определить отступ первой строки")

            # ── Отступ слева ─────────────────────────────────────
            left = h.get('left_indent')
            if left is not None and abs(left - exp['left']) > 0.1:
                issues.append(f"отступ слева: {left:.1f} см (должен {exp['left']} см)")

            # ── Отступ справа ────────────────────────────────────
            right = h.get('right_indent')
            if right is not None and abs(right - exp['right']) > 0.1:
                issues.append(f"отступ справа: {right:.1f} см (должен {exp['right']} см)")

            # ── Точка в конце ────────────────────────────────────
            if text.endswith('.'):
                issues.append("в конце заголовка не должно быть точки")

            if issues:
                pv = text[:50] + ('...' if len(text) > 50 else '')
                errors.append(f"'{pv}' (уровень {lv}): {', '.join(issues)}")

        if errors:
            return RuleResult(
                status='fail', summary=f'Нарушений: {len(errors)}', details=errors,
                received=f"Проблемных заголовков: {len(set(e.split(':')[0] for e in errors))}",
                expected="Times New Roman, полужирный, 18/16/14 пт, отступ 1.25 см, межстрочный 1.5, "
                         "интервалы по табл. 5.1, основные разделы ПРОПИСНЫМИ по центру"
            )

        return RuleResult(status='pass', summary='Оформление всех заголовков соответствует требованиям')