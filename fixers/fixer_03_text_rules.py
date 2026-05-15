"""Фиксер 03: прямые кавычки → «ёлочки», заглавная буква в ссылках."""

import re
from fixers.base_fixer import BaseFixer, FixResult

_REF_RE = re.compile(
    r'\b(рисунок|таблица|листинг)\s+(\d+\.\d+)',
    re.IGNORECASE | re.UNICODE
)


def _fix_quotes(para) -> int:
    """Заменяет прямые кавычки на «ёлочки» по всем runs параграфа."""
    in_quote = False
    changed = 0
    for run in para.runs:
        if '"' not in run.text:
            continue
        new_text = ''
        for ch in run.text:
            if ch == '"':
                if not in_quote:
                    new_text += '«'
                    in_quote = True
                else:
                    new_text += '»'
                    in_quote = False
                changed += 1
            else:
                new_text += ch
        try:
            run.text = new_text
        except Exception:
            pass
    return changed


def _fix_ref_caps(para) -> int:
    """Поднимает первую букву в «рисунок X.Y», «таблица X.Y», «листинг X.Y»."""
    changed = 0
    for run in para.runs:
        new_text = _REF_RE.sub(
            lambda m: m.group(1).capitalize() + ' ' + m.group(2),
            run.text
        )
        if new_text != run.text:
            try:
                run.text = new_text
                changed += 1
            except Exception:
                pass
    return changed


class TextRulesFixer(BaseFixer):
    @property
    def fixer_id(self): return "text_rules"

    @property
    def name(self): return "Правила текста"

    def fix(self, doc, model) -> FixResult:
        result = FixResult(fixer_id=self.fixer_id, name=self.name)
        total_quotes = 0
        total_caps = 0

        for para in doc.paragraphs:
            if not para.text.strip():
                continue
            total_quotes += _fix_quotes(para)
            total_caps += _fix_ref_caps(para)

        if total_quotes:
            result.changes.append(f"Заменено прямых кавычек: {total_quotes}")
        if total_caps:
            result.changes.append(f"Исправлена заглавная буква в ссылках: {total_caps}")

        if not result.changes:
            result.status = 'skipped'
        return result
