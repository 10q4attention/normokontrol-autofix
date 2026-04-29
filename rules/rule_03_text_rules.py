"""
Правило 03: Правила, распространяющиеся на весь текст.
Проверяет: кавычки (русский текст), нумерацию объектов, ссылки, окончания параграфов.
"""

import re
from .base_rule import BaseRule, RuleResult


class TextRulesRule(BaseRule):
    @property
    def rule_id(self): return "text_rules"
    @property
    def name(self): return "Правила оформления текста"
    @property
    def description(self): return "Проверка кавычек, нумерации объектов, ссылок, окончания параграфов"

    def check(self, model):
        errors = []

        all_text = ' '.join(e['text'] for e in model.elements if e['text'])

        # ── 3.5 Кавычки: русский текст должен быть в ёлочках ─────
        straight_quotes = re.findall(r'"([а-яёА-ЯЁ][^"]*[а-яёА-ЯЁ])"', all_text)
        if straight_quotes:
            errors.append(
                f"Обнаружены прямые кавычки (\") вместо ёлочек («») в русском тексте. "
                f"Пример: \"{straight_quotes[0][:50]}\""
            )

        # ── 3.10 Нумерация объектов ──────────────────────────────
        for cap in model.captions:
            m3 = re.match(r'(Рисунок|Таблица|Листинг)\s+(\d+\.\d+\.\d+)', cap['text'], re.I)
            if m3:
                errors.append(
                    f"Трёхуровневая нумерация в подписи: '{cap['text'][:60]}'. "
                    f"Должна быть двухуровневая (X.Y)."
                )

        # ── 3.11 Ссылки с большой буквы ──────────────────────────
        wrong_refs = re.findall(r'(?:рисунок|таблица|листинг|приложение)\s+\d+\.\d+', all_text, re.I)
        wrong_refs_lower = [r for r in wrong_refs if r[0].islower()]
        if wrong_refs_lower:
            errors.append(
                f"Ссылки на объекты должны быть с большой буквы. "
                f"Найдено: {', '.join(wrong_refs_lower[:3])}"
            )

        # ── 3.12 Не заканчивать параграф таблицей/рисунком/формулой ──
        for i, e in enumerate(model.elements):
            if e['is_heading'] and e['heading_level'] in (1, 2):
                prev = None
                for j in range(i-1, -1, -1):
                    if model.elements[j]['text'] or model.elements[j]['is_table'] or model.elements[j]['has_drawing']:
                        prev = model.elements[j]
                        break
                if prev and (prev['is_table'] or prev['has_drawing'] or prev['has_formula']):
                    obj_type = 'таблицей' if prev['is_table'] else 'рисунком' if prev['has_drawing'] else 'формулой'
                    errors.append(
                        f"Раздел '{e['text'][:50]}' начинается сразу после {obj_type}. "
                        f"После таблицы/рисунка/формулы должен быть текст."
                    )

        if errors:
            return RuleResult(
                status='fail', summary=f'Нарушений в тексте: {len(errors)}',
                details=errors,
                received=f"Проверен текст ({len(all_text)} символов)",
                expected="Кавычки-ёлочки для русского текста, ссылки с большой буквы, текст после объектов"
            )

        return RuleResult(
            status='pass',
            summary='Правила оформления текста соблюдены',
            received=f"Проверен текст ({len(all_text)} символов)"
        )