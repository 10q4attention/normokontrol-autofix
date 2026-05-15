"""Фиксер 12: листинги — код Courier New 10pt, подписи TNR 12 курсив по левому."""

import re
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from fixers.base_fixer import BaseFixer, FixResult

_W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
_LISTING_CAP_RE = re.compile(r'^Листинг\s+[\dА-ЯA-Z]+\.\d+', re.UNICODE)


def _has_border(para) -> bool:
    ppr = para._element.find(f'{{{_W}}}pPr')
    return ppr is not None and ppr.find(f'{{{_W}}}pBdr') is not None


def _is_code_paragraph(para) -> bool:
    style = (para.style.name or '').lower() if para.style else ''
    if 'листинг' in style or 'code' in style:
        return True
    if _has_border(para):
        return True
    for run in para.runs:
        if run.text.strip():
            fn = (run.font.name or '').lower()
            if 'courier' in fn:
                return True
            break
    return False


def _apply_code(para):
    pf = para.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.0

    for run in para.runs:
        if not run.text:
            continue
        run.font.name = 'Courier New'
        run.font.size = Pt(10)
        run.font.bold = False
        run.font.italic = False


def _apply_listing_caption(para):
    pf = para.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.5

    for run in para.runs:
        if not run.text:
            continue
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        run.font.italic = True
        run.font.bold = False


class ListingsFixer(BaseFixer):
    @property
    def fixer_id(self): return "listings"

    @property
    def name(self): return "Листинги кода"

    def fix(self, doc, model) -> FixResult:
        result = FixResult(fixer_id=self.fixer_id, name=self.name)
        fixed_caps = 0
        fixed_code = 0

        for para in doc.paragraphs:
            text = para.text.strip()
            if _LISTING_CAP_RE.match(text):
                _apply_listing_caption(para)
                fixed_caps += 1
            elif _is_code_paragraph(para) and text:
                _apply_code(para)
                fixed_code += 1

        if fixed_caps:
            result.changes.append(f"Исправлено подписей листингов: {fixed_caps}")
        if fixed_code:
            result.changes.append(f"Исправлено абзацев кода: {fixed_code}")

        if not result.changes:
            result.status = 'skipped'
        return result
