"""
Фиксер 06: структурные правки документа.
- Преобразует «Содержание»/«Оглавление» в заголовок 1 «ОГЛАВЛЕНИЕ»
- Исправляет уровень заголовков (X.Y → Heading 2, X.Y.Z → Heading 3)
  + применяет форматирование нового уровня (перекрывает то, что мог поставить fixer_05)
"""

import re
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from fixers.base_fixer import BaseFixer, FixResult

# Форматирование по уровню (тe же значения, что в fixer_05 _EXP)
_LEVEL_FMT = {
    2: {'size': 16, 'sb': 24, 'sa': 12, 'indent': 1.25},
    3: {'size': 14, 'sb': 24, 'sa': 12, 'indent': 1.25},
}

_L2_RE = re.compile(r'^\d+\.\d+[\.\s]')    # 1.2. или 1.2 текст
_L3_RE = re.compile(r'^\d+\.\d+\.\d+[\.\s]')  # 1.2.3. или 1.2.3 текст

_H1_STYLES = ('heading 1', 'заголовок 1')
_H2_STYLES = ('heading 2', 'заголовок 2')
_H3_STYLES = ('heading 3', 'заголовок 3')


def _get_style(doc, candidates):
    """Возвращает первый найденный стиль из списка кандидатов."""
    for name in doc.styles:
        if name.name.lower() in candidates:
            return name
    return None


def _is_heading1(para):
    style = (para.style.name or '').lower() if para.style else ''
    return any(s in style for s in _H1_STYLES)


def _apply_demoted_heading(para, level: int):
    """Применяет форматирование после смены уровня заголовка."""
    fmt = _LEVEL_FMT.get(level, _LEVEL_FMT[3])
    pf = para.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.first_line_indent = Cm(fmt['indent'])
    pf.left_indent = Pt(0)
    pf.space_before = Pt(fmt['sb'])
    pf.space_after = Pt(fmt['sa'])
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.5
    for run in para.runs:
        if not run.text:
            continue
        run.font.name = 'Times New Roman'
        run.font.size = Pt(fmt['size'])
        run.font.bold = True
        run.font.italic = False


class StructureFixer(BaseFixer):
    @property
    def fixer_id(self): return "structure"

    @property
    def name(self): return "Структура документа"

    def fix(self, doc, model) -> FixResult:
        result = FixResult(fixer_id=self.fixer_id, name=self.name)

        # ── 1. ОГЛАВЛЕНИЕ ────────────────────────────────────────────
        ogl_fixed = self._fix_ogl_heading(doc, model)
        if ogl_fixed:
            result.changes.append(f"Заголовок «ОГЛАВЛЕНИЕ» исправлен/добавлен")

        # ── 2. Уровни заголовков ─────────────────────────────────────
        h2_style = _get_style(doc, _H2_STYLES)
        h3_style = _get_style(doc, _H3_STYLES)

        fixed_to_h2, fixed_to_h3 = 0, 0

        for para in doc.paragraphs:
            if not _is_heading1(para):
                continue
            text = para.text.strip()
            if not text:
                continue

            if _L3_RE.match(text) and h3_style:
                para.style = h3_style
                _apply_demoted_heading(para, 3)
                fixed_to_h3 += 1
            elif _L2_RE.match(text) and h2_style:
                para.style = h2_style
                _apply_demoted_heading(para, 2)
                fixed_to_h2 += 1

        if fixed_to_h2:
            result.changes.append(f"Заголовки X.Y переведены на уровень 2: {fixed_to_h2}")
        if fixed_to_h3:
            result.changes.append(f"Заголовки X.Y.Z переведены на уровень 3: {fixed_to_h3}")

        if not result.changes:
            result.status = 'skipped'
        return result

    def _fix_ogl_heading(self, doc, model) -> bool:
        """
        Ищет параграф с текстом «Содержание» или «Оглавление»
        и превращает его в Heading 1 «ОГЛАВЛЕНИЕ».
        """
        h1_style = _get_style(doc, _H1_STYLES)
        if h1_style is None:
            return False

        for para in doc.paragraphs:
            text = para.text.strip().lower()
            if text in ('содержание', 'оглавление'):
                # Меняем стиль на Heading 1
                para.style = h1_style

                # Меняем текст всех runs на ОГЛАВЛЕНИЕ
                found_first = False
                for run in para.runs:
                    if run.text.strip() and not found_first:
                        run.text = 'ОГЛАВЛЕНИЕ'
                        found_first = True
                    elif run.text.strip():
                        run.text = ''

                # Если runs нет — параграф добавит текст через XML
                if not found_first:
                    from docx.oxml.ns import qn
                    from docx.oxml import OxmlElement
                    r = OxmlElement('w:r')
                    t = OxmlElement('w:t')
                    t.text = 'ОГЛАВЛЕНИЕ'
                    r.append(t)
                    para._element.append(r)

                # Форматирование самого заголовка
                pf = para.paragraph_format
                pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
                pf.space_before = Pt(0)
                pf.space_after = Pt(12)
                pf.first_line_indent = Cm(0)
                pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
                pf.line_spacing = 1.5

                for run in para.runs:
                    if run.text.strip():
                        run.font.name = 'Times New Roman'
                        run.font.size = Pt(18)
                        run.font.bold = True
                        run.font.italic = False

                return True

        return False
