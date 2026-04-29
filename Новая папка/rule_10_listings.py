import re
from .base_rule import BaseRule, RuleResult

class ListingsRule(BaseRule):
    @property
    def rule_id(self): return "listings"
    @property
    def name(self): return "Оформление листингов"
    @property
    def description(self): return "Проверка подписей, кода, рамки, ссылок"

    def check(self, model):
        errors = []
        caps = [c for c in model.captions if c['caption_type'] == 'listing']

        for cap in caps:
            text = cap['text']
            issues = []

            if '--' in text: issues.append("тире (—) вместо двух дефисов")
            elif re.search(r'\s-\s', text): issues.append("тире (—) вместо дефиса")
            if text.rstrip().endswith('.'): issues.append("точка в конце не нужна")

            if not cap.get('linked_code'):
                issues.append("не найден код листинга")

            fn = cap.get('font_name')
            if fn and 'times new roman' not in fn.lower(): issues.append(f"шрифт подписи: {fn}")
            fs = cap.get('font_size_pt')
            if fs and abs(fs-12)>0.5: issues.append(f"размер подписи: {fs:.0f} пт")
            if not cap.get('italic'): issues.append("подпись должна быть курсивом")
            if cap.get('alignment') is not None and cap['alignment']!=0:
                issues.append("выравнивание подписи по левому краю")
            sb = cap.get('space_before')
            if sb is not None and abs(sb-6)>2: issues.append(f"интервал перед: {sb:.0f} пт (нужен 6)")

            if not cap.get('has_border'):
                issues.append("код не оформлен в рамку")

            # Форматирование кода
            for code in cap.get('linked_code') or []:
                cfn = code.get('font_name')
                if cfn and 'courier new' not in cfn.lower(): issues.append(f"шрифт кода: {cfn}")
                cfs = code.get('font_size_pt')
                if cfs and abs(cfs-10)>0.5: issues.append(f"размер кода: {cfs:.0f} пт")
                if code.get('alignment') is not None and code['alignment']!=0:
                    issues.append("выравнивание кода по левому краю")
                break  # проверяем только первый блок

            if issues:
                pv = text[:70]+('...' if len(text)>70 else '')
                for iss in issues: errors.append(f"'{pv}': {iss}")

        # Нумерация
        secs = {}
        for cap in caps:
            m = re.match(r'^Листинг\s+([\dА-ЯA-Z]+)\.(\d+)\s+[—–\-]', cap['text'], re.I)
            if m:
                sid, num = m.group(1), m.group(2)
                if sid not in secs: secs[sid]=[]
                secs[sid].append((int(num), cap))
        for sid, lst in secs.items():
            lst.sort(key=lambda x: x[0])
            exp=1
            for n, cap in lst:
                if n!=exp: errors.append(f"'{cap['text'][:60]}': нумерация — ожидался {sid}.{exp}, найден {sid}.{n}")
                exp=n+1

        # Ссылки
        all_set = set()
        for cap in caps:
            m = re.match(r'^Листинг\s+([\dА-ЯA-Z]+)\.(\d+)', cap['text'], re.I)
            if m: all_set.add((m.group(1), m.group(2)))
        for sid, num in all_set:
            if not re.search(rf'\b[Лл]истинг(?:а|у|ом|е|и|ов|ам|ами|ах)?\s+{sid}\.{num}\b', model.body_text):
                errors.append(f"Нет ссылки на листинг {sid}.{num}")
        found = re.findall(r'[Лл]истинг(?:а|у|ом|е|и|ов|ам|ами|ах)?\s+([\dА-ЯA-Z]+)\.(\d+)', model.body_text)
        for rid, rn in found:
            if (rid, rn) not in all_set:
                errors.append(f"Ссылка на несуществующий листинг {rid}.{rn}")

        if errors:
            return RuleResult(status='fail', summary=f'Нарушений: {len(errors)}', details=errors,
                received=f"Листингов: {len(caps)}", expected="Листинг X.Y — Название, Courier New 10pt, рамка")
        return RuleResult(status='pass', summary=f'Листинги оформлены верно',
            received=f"Листингов: {len(caps)}")