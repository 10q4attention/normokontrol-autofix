"""Фиксер 04: основной текст — TNR 14, выравнивание, отступы, интервал 1.5."""

import re
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from fixers.base_fixer import BaseFixer, FixResult

_W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

_CAPTION_RE = re.compile(
    r'^(Таблица|Рисунок|Листинг|Продолжение\s+[Тт]аблицы)',
    re.UNICODE
)
_TOC_RE = re.compile(r'(\t\s*\d+\s*$|\.{2,}\s*\d+\s*$)')

_SKIP_STYLES = (
    'heading', 'заголовок',
    'toc', 'оглавление', 'contents',
    'caption', 'подпись',
    'листинг', 'code',
)


def _is_main_text(para) -> bool:
    style = (para.style.name or '').lower() if para.style else ''
    text = para.text.strip() if para.text else ''

    if not text:
        return False
    if any(s in style for s in _SKIP_STYLES):
        return False
    if _CAPTION_RE.match(text):
        return False
    if _TOC_RE.search(text) and len(text) < 150:
        return False
    # Список
    if para._element.find(f'.//{{{_W}}}numPr') is not None:
        return False
    # Код (Courier в первом непустом run)
    for run in para.runs:
        if run.text.strip():
            fn = (run.font.name or '').lower()
            if 'courier' in fn:
                return False
            break
    return True


def _apply_main_text(para):
    pf = para.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.first_line_indent = Cm(1.25)
    pf.left_indent = Pt(0)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.5

    for run in para.runs:
        if not run.text:
            continue
        run.font.name = 'Times New Roman'
        run.font.size = Pt(14)


class MainTextFixer(BaseFixer):
    @property
    def fixer_id(self): return "main_text"

    @property
    def name(self): return "Основной текст"

    def fix(self, doc, model) -> FixResult:
        result = FixResult(fixer_id=self.fixer_id, name=self.name)
        fixed = 0

        for para in doc.paragraphs:
            if _is_main_text(para):
                _apply_main_text(para)
                fixed += 1

        if fixed:
            result.changes.append(f"Исправлено абзацев основного текста: {fixed}")
        else:
            result.status = 'skipped'
        return result
