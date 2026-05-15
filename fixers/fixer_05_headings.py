"""Фиксер 05: заголовки — шрифт, размер, жирность, выравнивание, убрать точку."""

from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from fixers.base_fixer import BaseFixer, FixResult

_SPECIAL = {
    'ВВЕДЕНИЕ', 'ЗАКЛЮЧЕНИЕ',
    'СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ', 'СПИСОК ЛИТЕРАТУРЫ',
    'АННОТАЦИЯ', 'РЕФЕРАТ', 'СПИСОК ПРИНЯТЫХ СОКРАЩЕНИЙ',
}

_LEVEL_SIZE = {1: 18, 2: 16, 3: 14}

_HEADING_STYLES = (
    'heading 1', 'heading 2', 'heading 3',
    'заголовок 1', 'заголовок 2', 'заголовок 3',
)


def _heading_level(para) -> int | None:
    style = (para.style.name or '').lower() if para.style else ''
    for lvl in (1, 2, 3):
        if f'heading {lvl}' in style or f'заголовок {lvl}' in style:
            return lvl
    return None


def _remove_trailing_period(para):
    for run in reversed(para.runs):
        if run.text.strip():
            t = run.text.rstrip()
            if t.endswith('.'):
                run.text = t[:-1]
            break


def _apply_heading(para, level: int):
    text = para.text.strip().upper()
    is_special = text in _SPECIAL

    pf = para.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.5
    pf.first_line_indent = Cm(0)

    if is_special:
        pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif level == 1:
        pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    else:
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    size = Pt(_LEVEL_SIZE.get(level, 14))

    for run in para.runs:
        if not run.text:
            continue
        run.font.name = 'Times New Roman'
        run.font.size = size
        run.font.bold = True
        run.font.italic = False
        if is_special:
            run.text = run.text.upper()

    _remove_trailing_period(para)


class HeadingsFixer(BaseFixer):
    @property
    def fixer_id(self): return "headings"

    @property
    def name(self): return "Заголовки"

    def fix(self, doc, model) -> FixResult:
        result = FixResult(fixer_id=self.fixer_id, name=self.name)
        fixed = 0

        for para in doc.paragraphs:
            level = _heading_level(para)
            if level is None:
                continue
            _apply_heading(para, level)
            fixed += 1

        if fixed:
            result.changes.append(f"Исправлено заголовков: {fixed}")
        else:
            result.status = 'skipped'
        return result
