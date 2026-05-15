"""Фиксер 07: подписи к таблицам — TNR 12 курсив, по ширине, интервал перед 6pt."""

import re
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from fixers.base_fixer import BaseFixer, FixResult

_TABLE_CAP_RE = re.compile(
    r'^(?:Таблица|Продолжение\s+[Тт]аблицы)\s+[\dА-ЯA-Z]+\.\d+',
    re.UNICODE
)
# Дефис с пробелами → em-dash
def _fix_table_caption(para):
    pf = para.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.space_before = Pt(6)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.5

    for run in para.runs:
        if not run.text:
            continue
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        run.font.italic = True
        run.font.bold = False
        # Дефис может быть в отдельном run или внутри текста
        t = run.text
        if t.strip() == '-':
            run.text = t.replace('-', '—')
        elif ' - ' in t:
            run.text = t.replace(' - ', ' — ')


class TableCaptionFixer(BaseFixer):
    @property
    def fixer_id(self): return "table_captions"

    @property
    def name(self): return "Подписи таблиц"

    def fix(self, doc, model) -> FixResult:
        result = FixResult(fixer_id=self.fixer_id, name=self.name)
        fixed = 0

        for para in doc.paragraphs:
            if _TABLE_CAP_RE.match(para.text.strip()):
                _fix_table_caption(para)
                fixed += 1

        if fixed:
            result.changes.append(f"Исправлено подписей таблиц: {fixed}")
        else:
            result.status = 'skipped'
        return result
