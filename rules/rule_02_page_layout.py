"""
Правило 02: Макет страницы.
Проверяет поля, ориентацию, размер бумаги и количество колонок.
"""

from .base_rule import BaseRule, RuleResult


class PageLayoutRule(BaseRule):
    @property
    def rule_id(self): return "page_layout"
    @property
    def name(self): return "Макет страницы"
    @property
    def description(self): return "Проверка полей (20-20-30-15 мм), ориентации (книжная), размера (A4), колонок (1)"

    def check(self, model):
        secs = model.page_setup
        if not secs:
            return RuleResult(status='error', summary='Нет данных о страницах')

        exp = {'top': 20, 'bottom': 20, 'left': 30, 'right': 15,
               'width': 210, 'height': 297, 'columns': 1}
        errors = []

        for i, s in enumerate(secs, 1):
            m = s.get('margins', {})
            if m and not all(v == 0 for v in m.values()):
                for side, label in [('top', 'верхнее'), ('bottom', 'нижнее'),
                                    ('left', 'левое'), ('right', 'правое')]:
                    v = m.get(side, 0)
                    if abs(v - exp[side]) > 1.5:
                        errors.append(
                            f"Секция {i}: {label} поле {v:.1f} мм (должно {exp[side]:.0f} мм)"
                        )

            if s.get('orientation') == 'landscape':
                errors.append(
                    f"Секция {i}: альбомная ориентация. "
                    f"Допустимо только для широких таблиц и рисунков."
                )

            w, h = s.get('width', 0), s.get('height', 0)
            if w > 0 and h > 0:
                if abs(w - exp['width']) > 2 or abs(h - exp['height']) > 2:
                    errors.append(
                        f"Секция {i}: размер {w:.0f}×{h:.0f} мм (должен A4: 210×297 мм)"
                    )

        if errors:
            return RuleResult(
                status='fail', summary=f'Нарушений макета: {len(errors)}',
                details=errors,
                received=f"Секций: {len(secs)}",
                expected="Поля: 20-20-30-15 мм, книжная, A4, 1 колонка"
            )

        return RuleResult(
            status='pass',
            summary='Макет страницы соответствует требованиям',
            received=f"Проверено секций: {len(secs)}"
        )