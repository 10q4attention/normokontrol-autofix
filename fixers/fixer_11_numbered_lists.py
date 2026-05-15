"""Фиксер 11: нумерованные списки — TNR 14, по ширине."""

from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from fixers.base_fixer import BaseFixer, FixResult

_W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def _is_numbered_list(para) -> bool:
    num_pr = para._element.find(f'.//{{{_W}}}numPr')
    if num_pr is None:
        return False
    text = para.text.strip()
    # Числовой список: текст начинается с цифры
    if text and text[0].isdigit():
        return True
    return False


def _apply_numbered_list(para):
    pf = para.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.5

    for run in para.runs:
        if not run.text:
            continue
        run.font.name = 'Times New Roman'
        run.font.size = Pt(14)


class NumberedListFixer(BaseFixer):
    @property
    def fixer_id(self): return "numbered_lists"

    @property
    def name(self): return "Нумерованные списки"

    def fix(self, doc, model) -> FixResult:
        result = FixResult(fixer_id=self.fixer_id, name=self.name)
        fixed = 0

        for para in doc.paragraphs:
            if _is_numbered_list(para):
                _apply_numbered_list(para)
                fixed += 1

        if fixed:
            result.changes.append(f"Исправлено элементов нумерованного списка: {fixed}")
        else:
            result.status = 'skipped'
        return result
