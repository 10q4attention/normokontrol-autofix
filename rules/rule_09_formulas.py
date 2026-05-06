"""
Правило 09: Формулы.
Проверяет: нумерацию, ссылки в тексте, пояснения после формулы.
"""

import re
from .base_rule import BaseRule, RuleResult


class FormulasRule(BaseRule):
    @property
    def rule_id(self): return "formulas"
    @property
    def name(self): return "Формулы"
    @property
    def description(self): return "Проверка нумерации, ссылок и пояснений (раздел 9)"

    def check(self, model):
        errors = []
        formulas = model.formulas

        if not formulas:
            return RuleResult(status='pass', summary='Формулы не обнаружены')

        # 9.6 Нумерация в пределах раздела
        secs = {}
        for f in formulas:
            sid = f.get('section')
            num = f.get('number')
            if sid and num:
                if sid not in secs:
                    secs[sid] = []
                secs[sid].append((int(num), f))
            else:
                # Формула без номера — не ошибка, нумеруются только те, на которые есть ссылки
                pass

        for sid, lst in secs.items():
            lst.sort(key=lambda x: x[0])
            exp = 1
            for n, f in lst:
                if n != exp:
                    errors.append(
                        f"Формула '{f['text'][:50]}': нумерация — "
                        f"ожидалась ({sid}.{exp}), найдена ({sid}.{n})"
                    )
                exp = n + 1

        # 9.7 Ссылки в тексте
        all_numbered = set()
        for f in formulas:
            if f.get('section') and f.get('number'):
                all_numbered.add((f['section'], f['number']))

        for f in formulas:
            if f.get('section') and f.get('number'):
                # Находим элемент формулы в model.elements
                formula_elem = next((e for e in model.elements if e.get('has_formula') and f['text'][:30] in e.get('text', '')), None)
                if formula_elem:
                    body_before = ' '.join(
                        e['text'] for e in model.elements 
                        if e['index'] < formula_elem['index']
                        and e['text'] 
                        and not e.get('is_caption') 
                        and not e.get('is_toc') 
                        and not e.get('is_table')
                    )
                else:
                    body_before = model.body_text
                
                sid, num = f['section'], f['number']
                if not re.search(rf'формул[аыеойамих]*\s*\(?\s*{sid}\.{num}\s*\)?', body_before, re.I):
                    errors.append(f"Нет ссылки на формулу ({sid}.{num}) перед её появлением")

        # Ссылки на несуществующие (во всём тексте)
        found_refs = re.findall(r'формул[аыеойамих]*\s*\(?\s*(\d+)\.(\d+)\s*\)?', model.body_text, re.I)
        for rid, rn in found_refs:
            if (rid, rn) not in all_numbered:
                errors.append(f"Ссылка на несуществующую формулу ({rid}.{rn})")

        # 9.8 Пояснения после формулы
        for f_idx, f in enumerate(formulas):
            if f.get('section') and f.get('number'):
                # Ищем элемент с текстом «где» после формулы
                formula_elem = None
                for e in model.elements:
                    if e['has_formula'] and e.get('text') and f['text'][:30] in e['text']:
                        formula_elem = e
                        break

                if formula_elem:
                    found_where = False
                    for j in range(formula_elem['index'] + 1, min(len(model.elements), formula_elem['index'] + 5)):
                        next_elem = model.elements[j] if j < len(model.elements) else None
                        if next_elem and next_elem.get('text', '').lower().startswith('где'):
                            found_where = True
                            # Проверяем отсутствие двоеточия после «где»
                            if next_elem['text'].strip().startswith('где:'):
                                errors.append(
                                    f"После 'где' не должно быть двоеточия: '{next_elem['text'][:60]}'"
                                )
                            # Проверяем отсутствие абзацного отступа
                            indent = next_elem.get('first_line_indent')
                            if indent is not None and abs(indent) > 0.1:
                                errors.append(
                                    f"Пояснение после формулы должно быть без абзацного отступа: "
                                    f"'{next_elem['text'][:50]}'"
                                )
                            break

        if errors:
            return RuleResult(
                status='fail', summary=f'Нарушений в формулах: {len(errors)}', details=errors,
                received=f"Формул: {len(formulas)}, с номерами: {len(all_numbered)}",
                expected="Нумерация (X.Y) в скобках справа, ссылки в тексте, пояснение со слова «где»"
            )

        return RuleResult(
            status='pass',
            summary=f'Формулы оформлены правильно ({len(formulas)} шт.)',
            received=f"Формул: {len(formulas)}"
        )