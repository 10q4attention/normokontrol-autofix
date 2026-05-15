"""Фиксер 08: подписи к рисункам — TNR 12 полужирный, по центру, интервал после 6pt."""

import re
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from fixers.base_fixer import BaseFixer, FixResult

_FIG_CAP_RE = re.compile(
    r'^Рисунок\s+[\dА-ЯA-Z]+\.\d+',
    re.UNICODE
)
def _fix_figure_caption(para):
    pf = para.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.space_before = Pt(0)
    pf.space_after = Pt(6)
    pf.first_line_indent = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.0

    for run in para.runs:
        if not run.text:
            continue
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.italic = False
        t = run.text
        if t.strip() == '-':
            run.text = t.replace('-', '—')
        elif ' - ' in t:
            run.text = t.replace(' - ', ' — ')


class FigureCaptionFixer(BaseFixer):
    @property
    def fixer_id(self): return "figure_captions"

    @property
    def name(self): return "Подписи рисунков"

    def fix(self, doc, model) -> FixResult:
        result = FixResult(fixer_id=self.fixer_id, name=self.name)
        fixed = 0

        for para in doc.paragraphs:
            if _FIG_CAP_RE.match(para.text.strip()):
                _fix_figure_caption(para)
                fixed += 1

        if fixed:
            result.changes.append(f"Исправлено подписей рисунков: {fixed}")
        else:
            result.status = 'skipped'
        return result
