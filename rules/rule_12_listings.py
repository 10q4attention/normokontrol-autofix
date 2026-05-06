"""
Правило 12: Листинги.
Проверяет: подписи, форматирование кода, рамку, нумерацию, ссылки.
"""

import re
from .base_rule import BaseRule, RuleResult


class ListingsRule(BaseRule):
    @property
    def rule_id(self): return "listings"
    @property
    def name(self): return "Листинги"
    @property
    def description(self): return "Проверка подписей, форматирования кода, рамки, ссылок (раздел 12)"

    def check(self, model):
        errors = []
        caps = [c for c in model.captions if c['caption_type'] == 'listing']

        if not caps:
            return RuleResult(status='pass', summary='Листинги не найдены')

        for cap in caps:
            text = cap['text']
            issues = []

            # 12.2 Тире
            if '--' in text:
                issues.append("тире (—) вместо двух дефисов")
            elif re.search(r'\s-\s', text):
                issues.append("тире (—) вместо дефиса")

            # Точка в конце
            if text.rstrip().endswith('.'):
                issues.append("точка в конце не нужна")

            # Код не найден
            code_ids = cap.get('code_refs', [])
            if len(code_ids) == 0:
                issues.append("не найден код листинга")

            # 12.4 Рамка — проверяем в блоках кода
            has_border = False
            for code_id in code_ids:
                code_elem = self._find_by_id(model, code_id)
                if code_elem and code_elem.get('has_border'):
                    has_border = True
                    break
            if not has_border:
                issues.append("код не оформлен в рамку")

            # Форматирование подписи (табл. 12.1)
            fn = cap.get('font_name')
            if fn and 'times new roman' not in fn.lower():
                issues.append(f"шрифт подписи: {fn}")

            fs = cap.get('font_size_pt')
            if fs is not None and abs(fs - 12) > 0.5:
                issues.append(f"размер подписи: {fs:.0f} пт (нужен 12)")

            if not cap.get('italic'):
                issues.append("подпись должна быть курсивом")

            if cap.get('alignment') is not None and cap['alignment'] != 0:
                issues.append("выравнивание подписи по левому краю")

            sb = cap.get('space_before')
            if sb is not None and abs(sb - 6) > 2:
                issues.append(f"интервал перед подписью: {sb:.0f} пт (нужен 6)")

            sa = cap.get('space_after')
            if sa is not None and abs(sa - 0) > 2:
                issues.append(f"интервал после подписи: {sa:.0f} пт (нужен 0)")

            ls = cap.get('line_spacing')
            if ls is not None and isinstance(ls, (int, float)) and abs(ls - 1.0) > 0.1:
                issues.append(f"междустрочный подписи: {ls:.2f} (нужен 1.0)")

            fi = cap.get('first_line_indent')
            if fi is not None and abs(fi) > 0.1:
                issues.append(f"отступ первой строки подписи: {fi:.1f} см (должен 0)")

            # Форматирование кода (табл. 12.2)
            for code_id in code_ids[:1]:
                code_elem = self._find_by_id(model, code_id)
                if code_elem:
                    cfn = code_elem.get('font_name')
                    if cfn and 'courier new' not in cfn.lower():
                        issues.append(f"шрифт кода: {cfn} (нужен Courier New)")

                    cfs = code_elem.get('font_size_pt')
                    if cfs is not None and abs(cfs - 10) > 0.5:
                        issues.append(f"размер кода: {cfs:.0f} пт (нужен 10)")

                    if code_elem.get('alignment') is not None and code_elem['alignment'] != 0:
                        issues.append("выравнивание кода по левому краю")

            if issues:
                pv = text[:70] + ('...' if len(text) > 70 else '')
                for iss in issues:
                    errors.append(f"'{pv}': {iss}")

        # Нумерация
        secs = {}
        for cap in caps:
            m = re.match(r'^Листинг\s+([\dА-ЯA-Z]+)\.(\d+)', cap['text'], re.I)
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
        for cap in caps:
            m = re.match(r'^Листинг\s+([\dА-ЯA-Z]+)\.(\d+)', cap['text'], re.I)
            if m:
                sid, num = m.group(1), m.group(2)
                all_set.add((sid, num))
                body_before = ' '.join(
                    e['text'] for e in model.elements 
                    if e['index'] < cap['index']
                    and e['text'] 
                    and not e.get('is_caption') 
                    and not e.get('is_toc') 
                    and not e.get('is_table')
                )
                if not re.search(rf'\b[Лл]истинг(?:а|у|ом|е|и|ов|ам|ами|ах)?\s+{sid}\.{num}\b', body_before):
                    errors.append(f"Нет ссылки на листинг {sid}.{num} перед его появлением")

        # Ссылки на несуществующие (во всём тексте)
        found = re.findall(r'[Лл]истинг(?:а|у|ом|е|и|ов|ам|ами|ах)?\s+([\dА-ЯA-Z]+)\.(\d+)', model.body_text)
        for rid, rn in found:
            if (rid, rn) not in all_set:
                errors.append(f"Ссылка на несуществующий листинг {rid}.{rn}")

        if errors:
            return RuleResult(
                status='fail', summary=f'Нарушений в листингах: {len(errors)}', details=errors,
                received=f"Листингов: {len(caps)}",
                expected="Листинг X.Y — Название, Courier New 10pt, рамка, формат по табл. 12.1-12.2"
            )

        return RuleResult(
            status='pass',
            summary=f'Листинги оформлены правильно ({len(caps)} шт.)',
            received=f"Листингов: {len(caps)}"
        )

    def _find_by_id(self, model, eid):
        if eid is None:
            return None
        for e in model.elements:
            if e['id'] == eid:
                return e
        return None