"""
Правило 08: Рисунки.
Проверяет: подписи, форматирование, нумерацию, ссылки.
"""

import re
from .base_rule import BaseRule, RuleResult


class FiguresRule(BaseRule):
    @property
    def rule_id(self): return "figures"
    @property
    def name(self): return "Рисунки"
    @property
    def description(self): return "Проверка подписей, форматирования, нумерации, ссылок (раздел 8)"

    def check(self, model):
        errors = []
        drawings = model.drawings
        captions = [c for c in model.captions if c['caption_type'] == 'figure']

        # Рисунки без подписей
        for d in drawings:
            if not d.get('linked_from'):
                errors.append("Рисунок без подписи")

        # Подписи без рисунков
        for cap in captions:
            if not cap.get('linked_to'):
                errors.append(f"Подпись без рисунка: '{cap['text'][:60]}'")

        # Проверяем подписи
        for cap in captions:
            text = cap['text']
            issues = []

            # 8.2 Тире
            if '--' in text:
                issues.append("тире (—) вместо двух дефисов")
            elif re.search(r'\s-\s', text):
                issues.append("тире (—) вместо дефиса")

            # Точка в конце
            if text.rstrip().endswith('.'):
                issues.append("точка в конце не нужна")

            # Сокращение
            if re.match(r'^Рис\.\s+', text, re.I):
                issues.append("не сокращать «Рисунок» до «Рис.»")

            # Трёхуровневая нумерация
            if re.search(r'^Рис(?:унок|\.)\s+\d+\.\d+\.\d+', text, re.I):
                issues.append("трёхуровневая нумерация не допускается")

            # Форматирование подписи (табл. 8.1)
            fn = cap.get('font_name')
            if fn and 'times new roman' not in fn.lower():
                issues.append(f"шрифт: {fn}")

            fs = cap.get('font_size_pt')
            if fs is not None and abs(fs - 12) > 0.5:
                issues.append(f"размер: {fs:.0f} пт (нужен 12)")

            if not cap.get('bold'):
                issues.append("должен быть полужирным")

            if cap.get('alignment') is not None and cap['alignment'] != 1:
                issues.append("выравнивание по центру")

            sb = cap.get('space_before')
            if sb is not None and abs(sb - 0) > 2:
                issues.append(f"интервал перед: {sb:.0f} пт (нужен 0)")

            sa = cap.get('space_after')
            if sa is not None and abs(sa - 6) > 2:
                issues.append(f"интервал после: {sa:.0f} пт (нужен 6)")

            ls = cap.get('line_spacing')
            if ls is not None and isinstance(ls, (int, float)) and abs(ls - 1.0) > 0.1:
                issues.append(f"междустрочный: {ls:.2f} (нужен 1.0)")

            fi = cap.get('first_line_indent')
            if fi is not None and abs(fi) > 0.1:
                issues.append(f"отступ первой строки: {fi:.1f} см (должен 0)")

            if issues:
                pv = text[:70] + ('...' if len(text) > 70 else '')
                for iss in issues:
                    errors.append(f"'{pv}': {iss}")

        # Нумерация
        secs = {}
        for cap in captions:
            m = re.match(r'^Рис(?:унок|\.)\s+([\dА-ЯA-Z]+)\.(\d+)', cap['text'], re.I)
            if m:
                sid, num = m.group(1), m.group(2)
                if sid not in secs:
                    secs[sid] = []
                secs[sid].append((int(num), cap))
        for sid, lst in secs.items():
            lst.sort(key=lambda x: x[0])
            exp = 1
            for n, cap in lst:
                if n != exp:
                    errors.append(f"'{cap['text'][:60]}': нумерация — ожидался {sid}.{exp}, найден {sid}.{n}")
                exp = n + 1

        # Ссылки
        all_set = set()
        for cap in captions:
            m = re.match(r'^Рис(?:унок|\.)\s+([\dА-ЯA-Z]+)\.(\d+)', cap['text'], re.I)
            if m:
                all_set.add((m.group(1), m.group(2)))
        for sid, num in all_set:
            if not re.search(rf'\b[Рр]исун(?:ок|ка|ку|ком|ке|ки|ков|кам|ками|ках)?\s+{sid}\.{num}\b', model.body_text):
                errors.append(f"Нет ссылки на рисунок {sid}.{num}")
        found = re.findall(r'[Рр]исун(?:ок|ка|ку|ком|ке|ки|ков|кам|ками|ках)?\s+([\dА-ЯA-Z]+)\.(\d+)', model.body_text)
        for rid, rn in found:
            if (rid, rn) not in all_set:
                errors.append(f"Ссылка на несуществующий рисунок {rid}.{rn}")

        if errors:
            return RuleResult(
                status='fail', summary=f'Нарушений в рисунках: {len(errors)}', details=errors,
                received=f"Рисунков: {len(drawings)}, подписей: {len(captions)}",
                expected="Рисунок X.Y — Название, формат по табл. 8.1"
            )
        return RuleResult(
            status='pass', summary=f'Рисунки оформлены правильно',
            received=f"Рисунков: {len(drawings)}"
        )