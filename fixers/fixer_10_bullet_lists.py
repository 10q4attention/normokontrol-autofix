"""Фиксер 10: маркированные списки — TNR 14, по ширине."""

from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from fixers.base_fixer import BaseFixer, FixResult

_W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def _is_bullet_list(para) -> bool:
    """Список с маркером-буллетом (не числовой)."""
    num_pr = para._element.find(f'.//{{{_W}}}numPr')
    if num_pr is None:
        return False
    # Определяем тип: ищем numId и смотрим на abstractNum
    # Упрощение: если первый символ текста — тире или маркер, считаем маркированным
    text = para.text.strip()
    if text.startswith('—') or text.startswith('–') or text.startswith('-') or text.startswith('•'):
        return True
    # Если не начинается с цифры — скорее всего маркированный
    if text and not text[0].isdigit():
        return True
    return False


def _apply_bullet_list(para):
    pf = para.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.5
    pf.first_line_indent = Cm(1.25)  # п.10.1: отступ маркера 1.25 см
    pf.left_indent = Cm(0)           # п.10.1: отступ слева 0

    for run in para.runs:
        if not run.text:
            continue
        run.font.name = 'Times New Roman'
        run.font.size = Pt(14)


class BulletListFixer(BaseFixer):
    @property
    def fixer_id(self): return "bullet_lists"

    @property
    def name(self): return "Маркированные списки"

    def fix(self, doc, model) -> FixResult:
        result = FixResult(fixer_id=self.fixer_id, name=self.name)
        fixed = 0

        for para in doc.paragraphs:
            if _is_bullet_list(para):
                _apply_bullet_list(para)
                fixed += 1

        if fixed:
            result.changes.append(f"Исправлено элементов маркированного списка: {fixed}")
        else:
            result.status = 'skipped'
        return result
