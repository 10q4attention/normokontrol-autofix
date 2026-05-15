"""Фиксер 02: поля страницы 20-20-30-15 мм, размер A4."""

from docx.shared import Mm
from fixers.base_fixer import BaseFixer, FixResult


class PageLayoutFixer(BaseFixer):
    @property
    def fixer_id(self): return "page_layout"

    @property
    def name(self): return "Макет страницы"

    def fix(self, doc, model) -> FixResult:
        result = FixResult(fixer_id=self.fixer_id, name=self.name)
        expected = {'top': 20, 'bottom': 20, 'left': 30, 'right': 15}

        for i, section in enumerate(doc.sections, 1):
            # Поля в мм через Mm() (python-docx принимает EMU, Mm() конвертирует)
            actual_top = section.top_margin.mm if section.top_margin else 0
            actual_bottom = section.bottom_margin.mm if section.bottom_margin else 0
            actual_left = section.left_margin.mm if section.left_margin else 0
            actual_right = section.right_margin.mm if section.right_margin else 0

            fixes_in_section = []

            if abs(actual_top - expected['top']) > 1.5:
                section.top_margin = Mm(expected['top'])
                fixes_in_section.append(f"верхнее поле {actual_top:.1f}→{expected['top']} мм")
            if abs(actual_bottom - expected['bottom']) > 1.5:
                section.bottom_margin = Mm(expected['bottom'])
                fixes_in_section.append(f"нижнее поле {actual_bottom:.1f}→{expected['bottom']} мм")
            if abs(actual_left - expected['left']) > 1.5:
                section.left_margin = Mm(expected['left'])
                fixes_in_section.append(f"левое поле {actual_left:.1f}→{expected['left']} мм")
            if abs(actual_right - expected['right']) > 1.5:
                section.right_margin = Mm(expected['right'])
                fixes_in_section.append(f"правое поле {actual_right:.1f}→{expected['right']} мм")

            # Размер бумаги A4
            w = section.page_width.mm if section.page_width else 0
            h = section.page_height.mm if section.page_height else 0
            if section.orientation and section.orientation.name == 'PORTRAIT':
                if abs(w - 210) > 2 or abs(h - 297) > 2:
                    section.page_width = Mm(210)
                    section.page_height = Mm(297)
                    fixes_in_section.append(f"размер бумаги {w:.0f}×{h:.0f}→210×297 мм (A4)")

            if fixes_in_section:
                result.changes.append(f"Секция {i}: " + ", ".join(fixes_in_section))

        if not result.changes:
            result.status = 'skipped'
        return result
