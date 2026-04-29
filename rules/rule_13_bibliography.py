"""
Правило 13: Список использованных источников.
Проверяет: нумерацию, форматирование, ссылки в тексте.
"""

import re
from .base_rule import BaseRule, RuleResult


class BibliographyRule(BaseRule):
    @property
    def rule_id(self): return "bibliography"
    @property
    def name(self): return "Список источников"
    @property
    def description(self): return "Проверка оформления списка источников и ссылок (раздел 13)"

    def check(self, model):
        errors = []

        # Находим заголовок
        biblio_heading = None
        for h in model.headings:
            if h['heading_level'] == 1 and h['text'].upper() == 'СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ':
                biblio_heading = h
                break

        if not biblio_heading:
            return RuleResult(
                status='fail',
                summary='Раздел не найден',
                details=['Добавьте раздел с заголовком первого уровня «СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ»'],
                expected="Заголовок первого уровня"
            )

        start_idx = biblio_heading['index']

        # Собираем ВСЕ элементы после заголовка
        candidates = []
        for e in model.elements:
            if e['index'] <= start_idx:
                continue
            if not e['text']:
                continue
            if e['is_heading'] and e['heading_level'] == 1:
                break
            if re.match(r'^Приложение\s+[А-ЯA-Z]', e['text'], re.I):
                break
            candidates.append(e)

        # Отбираем подряд идущие с правильной нумерацией
        items = []
        expected_num = 1
        for c in candidates:
            text = c['text']
            if not text:
                continue
            m = re.match(r'^(\d+)[\.\s]', text)
            if m:
                num = int(m.group(1))
                if num == expected_num:
                    items.append(c)
                    expected_num += 1
                else:
                    break
            elif c.get('is_list_item'):
                items.append(c)
                expected_num += 1
            else:
                break

        if not items:
            return RuleResult(
                status='fail',
                summary='Список источников пуст',
                details=['Добавьте пронумерованные источники'],
                expected="Не менее одного источника"
            )

        # Нумерация
        exp = 1
        for item in items:
            m = re.match(r'^(\d+)', item['text'])
            if m:
                n = int(m.group(1))
                if n != exp:
                    errors.append(f"Нумерация: ожидался {exp}, найден {n} ('{item['text'][:60]}')")
                exp = n + 1
            else:
                exp += 1

        # Форматирование
        for item in items:
            pv = item['text'][:50] + ('...' if len(item['text']) > 50 else '')
            fn = item.get('font_name')
            if fn and 'times new roman' not in fn.lower():
                errors.append(f"'{pv}': шрифт {fn}")
            fs = item.get('font_size_pt')
            if fs is not None and abs(fs - 14) > 0.5:
                errors.append(f"'{pv}': размер {fs:.0f} пт")
            if item.get('alignment') is not None and item['alignment'] != 3:
                errors.append(f"'{pv}': выравнивание по ширине")
            ls = item.get('line_spacing')
            if ls is not None and isinstance(ls, (int, float)) and abs(ls - 1.5) > 0.1:
                errors.append(f"'{pv}': междустрочный {ls:.2f}")
            indent = item.get('first_line_indent')
            if indent is not None and abs(indent - 1.25) > 0.2:
                errors.append(f"'{pv}': отступ первой строки {indent:.2f} см")

        # Ссылки
        body_refs = self._extract_refs(model.body_text)
        expected = set(range(1, len(items) + 1))
        for n in sorted(expected - body_refs):
            errors.append(f"На источник [{n}] нет ссылки в тексте")
        for n in sorted(body_refs - expected)[:5]:
            errors.append(f"Ссылка на несуществующий источник [{n}]")
        if len(body_refs - expected) > 5:
            errors.append(f"... и ещё {len(body_refs - expected) - 5} несуществующих ссылок")

        if errors:
            return RuleResult(
                status='fail', summary=f'Нарушений: {len(errors)}', details=errors,
                received=f"Источников: {len(items)}",
                expected="Нумерация, Times New Roman 14pt, по ширине, отступ 1.25, ссылки в квадратных скобках"
            )

        return RuleResult(
            status='pass',
            summary=f'Список источников оформлен правильно ({len(items)} источников)',
            received=f"Источников: {len(items)}"
        )

    def _extract_refs(self, text):
        refs = set()
        for b in re.findall(r'\[([^\]]+)\]', text):
            clean = b
            for marker in ['с.', 'c.', 'стр.']:
                idx = clean.find(marker)
                if idx > 0:
                    clean = clean[:idx]
                    break
            for n in re.findall(r'\d+', clean):
                refs.add(int(n))
        return refs