import re
from .base_rule import BaseRule, RuleResult

class FormulasRule(BaseRule):
    @property
    def rule_id(self): return "formulas"
    @property
    def name(self): return "Формулы"
    @property
    def description(self): return "Проверка нумерации и ссылок"

    def check(self, model):
        errors = []
        formulas = model.formulas

        if not formulas:
            return RuleResult(status='pass', summary='Формулы не обнаружены')

        secs = {}
        for f in formulas:
            sid = f.get('section')
            num = f.get('number')
            if sid and num:
                if sid not in secs: secs[sid] = []
                secs[sid].append((int(num), f))
            else:
                errors.append(f"Формула '{f['text'][:60]}': не пронумерована")

        for sid, lst in secs.items():
            lst.sort(key=lambda x: x[0])
            exp = 1
            for n, f in lst:
                if n != exp:
                    errors.append(f"Формула '{f['text'][:60]}': нумерация — ожидалась ({sid}.{exp}), найдена ({sid}.{n})")
                exp = n + 1

        all_set = set()
        for f in formulas:
            if f.get('section') and f.get('number'):
                all_set.add((f['section'], f['number']))
        for sid, num in all_set:
            if not re.search(rf'формул[аыеойамих]*\s*\(?\s*{sid}\.{num}\s*\)?', model.body_text, re.I):
                errors.append(f"Нет ссылки на формулу ({sid}.{num})")

        refs = re.findall(r'\(?\s*(\d+)\.(\d+)\s*\)?\s*', model.body_text)
        for rid, rn in refs:
            if (rid, rn) not in all_set:
                errors.append(f"Ссылка на несуществующую формулу ({rid}.{rn})")

        if errors:
            return RuleResult(status='fail', summary=f'Нарушений: {len(errors)}', details=errors,
                received=f"Формул: {len(formulas)}",
                expected="Нумерация (X.Y) справа, ссылки в тексте")
        return RuleResult(status='pass', summary=f'Формулы оформлены верно',
            received=f"Формул: {len(formulas)}")