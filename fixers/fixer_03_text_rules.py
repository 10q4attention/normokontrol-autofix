"""Фиксер 03: прямые кавычки → «ёлочки» (рус) / "" (англ), заглавная в ссылках."""

import re
from fixers.base_fixer import BaseFixer, FixResult

_REF_RE = re.compile(
    r'\b(рисунок|таблица|листинг)\s+(\d+\.\d+)',
    re.IGNORECASE | re.UNICODE
)

_OPEN_ENG  = '“'  # "
_CLOSE_ENG = '”'  # "


def _is_russian(text: str) -> bool:
    """Русский контекст: есть хоть одна кириллица или нет букв вообще."""
    if any('Ѐ' <= c <= 'ӿ' for c in text):
        return True
    return not any(c.isalpha() for c in text)


def _fix_quotes(para) -> int:
    """Заменяет прямые кавычки: русский текст → «», английский → ""."""
    # Собираем весь текст параграфа и маппинг позиция → (run_idx, char_idx)
    full = []
    positions = []
    for ri, run in enumerate(para.runs):
        for ci, ch in enumerate(run.text):
            full.append(ch)
            positions.append((ri, ci))

    full_str = ''.join(full)
    if '"' not in full_str:
        return 0

    replacements = {}  # позиция в full_str → символ замены
    i = 0
    while i < len(full_str):
        if full_str[i] == '"':
            j = full_str.find('"', i + 1)
            if j == -1:
                # Незакрытая кавычка — ставим открывающую по языку следующего текста
                replacements[i] = '«' if _is_russian(full_str[i+1:]) else _OPEN_ENG
                break
            content = full_str[i+1:j]
            if _is_russian(content):
                replacements[i] = '«'
                replacements[j] = '»'
            else:
                replacements[i] = _OPEN_ENG
                replacements[j] = _CLOSE_ENG
            i = j + 1
        else:
            i += 1

    if not replacements:
        return 0

    # Применяем замены обратно в runs
    run_chars = [list(run.text) for run in para.runs]
    for pos, new_ch in replacements.items():
        ri, ci = positions[pos]
        run_chars[ri][ci] = new_ch

    for ri, run in enumerate(para.runs):
        new_text = ''.join(run_chars[ri])
        if new_text != run.text:
            try:
                run.text = new_text
            except Exception:
                pass

    return len(replacements)


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
