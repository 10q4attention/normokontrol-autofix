import re
from .base_rule import BaseRule, RuleResult

class HeadingsLevel3Rule(BaseRule):
    @property
    def rule_id(self): return "headings_level3"
    @property
    def name(self): return "Заголовки третьего уровня"
    @property
    def description(self): return "Проверка нумерации пунктов"

    def check(self, model):
        l2 = [h for h in model.headings if h['level']==2]
        l3 = [h for h in model.headings if h['level']==3]
        if not l2:
            return RuleResult(status='fail', summary='Нет заголовков 2 уровня')
        errors = []
        for h3 in l3:
            n = re.match(r'^(\d+\.\d+)\.(\d+)', h3['text'])
            if n:
                pn, pt = n.group(1), n.group(2)
                if not any(re.match(rf'^{pn}[\.\s]', h['text']) for h in l2):
                    errors.append(f"'{h3['text'][:60]}': не найден подраздел {pn}")
                else:
                    sib = sorted([h for h in l3 if re.match(rf'^{pn}\.(\d+)', h['text'])],
                                 key=lambda x: int(re.match(rf'^{pn}\.(\d+)', x['text']).group(1)))
                    pos = next(i for i,s in enumerate(sib) if s is h3)
                    if pos>0:
                        prev = int(re.match(rf'^{pn}\.(\d+)', sib[pos-1]['text']).group(1))
                        if int(pt)!=prev+1:
                            errors.append(f"Нарушение: после {pn}.{prev} идёт {pn}.{pt}")
            else:
                errors.append(f"Неверный формат: '{h3['text'][:60]}'")
        if errors:
            return RuleResult(status='fail', summary=f'Ошибок: {len(errors)}', details=errors,
                received=f"Пунктов: {len(l3)}", expected="X.Y.Z, последовательная нумерация")
        if not l3:
            return RuleResult(status='pass', summary='Пункты отсутствуют')
        return RuleResult(status='pass', summary=f'Все {len(l3)} пунктов верны')