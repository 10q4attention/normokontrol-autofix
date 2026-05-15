"""Фиксер 05: заголовки — шрифт, размер, жирность, выравнивание, убрать точку."""

from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from fixers.base_fixer import BaseFixer, FixResult

_MAIN_SECTIONS = {
    'аннотация', 'оглавление', 'содержание', 'введение', 'заключение',
    'список использованных источников', 'список литературы',
    'список используемых сокращений и обозначений', 'приложения', 'реферат',
}

# Точные значения из rule_05 EXP
_EXP = {
    1: {'size': 18, 'sb': 0,  'sa': 12, 'indent': 1.25, 'indent_main': 0},
    2: {'size': 16, 'sb': 24, 'sa': 12, 'indent': 1.25},
    3: {'size': 14, 'sb': 24, 'sa': 12, 'indent': 1.25},
}


def _heading_level(para):
    style = (para.style.name or '').lower() if para.style else ''
    for lvl in (1, 2, 3):
        if f'heading {lvl}' in style or f'заголовок {lvl}' in style:
            return lvl
    return None


def _is_main_section(text: str) -> bool:
    return any(s in text.lower() for s in _MAIN_SECTIONS)


def _remove_trailing_period(para):
    for run in reversed(para.runs):
        if run.text.strip():
            t = run.text.rstrip()
            if t.endswith('.'):
                run.text = t[:-1]
            break


def _apply_heading(para, level: int):
    exp = _EXP.get(level, _EXP[3])
    text = para.text.strip()
    is_main = _is_main_section(text)

    pf = para.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.5
    pf.space_before = Pt(exp['sb'])
    pf.space_after = Pt(exp['sa'])
    pf.left_indent = Pt(0)

    if is_main:
        pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf.first_line_indent = Cm(exp.get('indent_main', 0))
    else:
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf.first_line_indent = Cm(exp['indent'])

    size = Pt(exp['size'])

    for run in para.runs:
        if not run.text:
            continue
        run.font.name = 'Times New Roman'
        run.font.size = size
        run.font.bold = True
        run.font.italic = False
        if is_main:
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
