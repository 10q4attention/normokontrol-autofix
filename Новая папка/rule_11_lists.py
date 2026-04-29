import re
from .base_rule import BaseRule, RuleResult

class ListsRule(BaseRule):
    @property
    def rule_id(self): return "lists"
    @property
    def name(self): return "Списки"
    @property
    def description(self): return "Проверка оформления маркированных и нумерованных списков"

    def check(self, model):
        errors = []
        items = model.list_items

        if not items:
            return RuleResult(status='pass', summary='Списки не найдены')

        # Группируем последовательные элементы
        groups = []
        cur = [items[0]]
        for i in range(1, len(items)):
            if items[i]['para_index'] == cur[-1]['para_index'] + 1:
                cur.append(items[i])
            else:
                groups.append(cur)
                cur = [items[i]]
        groups.append(cur)

        for group in groups:
            first_text = group[0]['text']
            is_bullet = bool(re.match(r'^[—–\-]', first_text))
            label = 'Маркированный' if is_bullet else 'Нумерованный'

            for idx, item in enumerate(group):
                text = item['text']
                pv = text[:50] + ('...' if len(text) > 50 else '')

                # ── Маркер ────────────────────────────────────────
                if is_bullet:
                    if text.startswith('--'):
                        errors.append(f"{label} '{pv}': тире (—) вместо двух дефисов")
                    elif text.startswith('-') and not text.startswith('—') and not text.startswith('–'):
                        errors.append(f"{label} '{pv}': тире (—) вместо дефиса")
                else:
                    if re.match(r'^\d+\)', text):
                        errors.append(f"{label} '{pv}': точка после номера, а не скобка")

                # ── Пунктуация ────────────────────────────────────
                if is_bullet:
                    content = re.sub(r'^[—–\-]\s*', '', text)
                    if content:
                        if content[0].isalpha() and content[0].isupper():
                            errors.append(f"{label} '{pv}': текст должен начинаться со строчной буквы")
                        is_last = (idx == len(group) - 1)
                        if is_last:
                            if not content.rstrip().endswith('.'):
                                errors.append(f"{label} '{pv}': последний элемент должен заканчиваться точкой")
                        else:
                            if not content.rstrip().endswith(';'):
                                errors.append(f"{label} '{pv}': элемент должен заканчиваться точкой с запятой")
                else:
                    content = re.sub(r'^\d+[\.\)]\s*', '', text)
                    if content:
                        if content[0].isalpha() and content[0].islower():
                            errors.append(f"{label} '{pv}': текст должен начинаться с прописной буквы")
                        if not content.rstrip().endswith('.'):
                            errors.append(f"{label} '{pv}': элемент должен заканчиваться точкой")

                # ── Форматирование ───────────────────────────────
                # Шрифт Times New Roman 14pt
                fn = item.get('font_name')
                if fn and 'times new roman' not in fn.lower():
                    errors.append(f"{label} '{pv}': шрифт {fn} (нужен Times New Roman)")

                fs = item.get('font_size_pt')
                if fs and abs(fs - 14) > 0.5:
                    errors.append(f"{label} '{pv}': размер {fs:.0f} пт (нужен 14 пт)")

                # Выравнивание по ширине
                if item.get('alignment') is not None and item['alignment'] != 3:
                    errors.append(f"{label} '{pv}': выравнивание должно быть по ширине")

                # Межстрочный полуторный
                ls = item.get('line_spacing')
                if ls is not None:
                    if isinstance(ls, float) and abs(ls - 1.5) > 0.1:
                        errors.append(f"{label} '{pv}': междустрочный {ls:.2f} (нужен 1.5)")

                # Интервал перед 0 пт
                sb = item.get('space_before')
                if sb is not None and abs(sb - 0) > 2:
                    errors.append(f"{label} '{pv}': интервал перед {sb:.0f} пт (нужен 0 пт)")

                # Интервал после 0 пт
                sa = item.get('space_after')
                if sa is not None and abs(sa - 0) > 2:
                    errors.append(f"{label} '{pv}': интервал после {sa:.0f} пт (нужен 0 пт)")

                # ── Отступы ──────────────────────────────────────
                # Отступ слева: 0 см
                left_indent = item.get('left_indent')
                if left_indent is not None and abs(left_indent - 0) > 0.1:
                    errors.append(f"{label} '{pv}': отступ слева {left_indent:.1f} см (должен 0 см)")

                # Отступ маркера: 1.25 см + табуляция текста: 2.25 см
                # В Word это реализуется через first_line_indent (отрицательный выступ)
                # и left_indent (позиция текста)
                # Маркер на 1.25 см, текст на 2.25 см
                # Ожидаем: first_line_indent ≈ -1.0 см (2.25 - 1.25)
                #          left_indent ≈ 2.25 см
                # Но методичка говорит: отступ слева 0 см
                # Значит: left_indent = 0, first_line_indent = 1.25 см
                first_indent = item.get('first_line_indent')
                if first_indent is not None:
                    if abs(first_indent - 1.25) > 0.3:
                        errors.append(f"{label} '{pv}': отступ первой строки {first_indent:.1f} см (должен 1.25 см)")

        if errors:
            return RuleResult(
                status='fail',
                summary=f'Нарушений в списках: {len(errors)}',
                details=errors,
                received=f"Групп списков: {len(groups)}, элементов: {len(items)}",
                expected="Маркированные: тире (—), строчная, точка с запятой, последний — точка. "
                         "Нумерованные: прописная, точка. "
                         "Times New Roman 14pt, по ширине, межстрочный 1.5, "
                         "отступ маркера 1.25 см, отступ слева 0 см."
            )

        return RuleResult(
            status='pass',
            summary=f'Списки оформлены верно ({len(groups)} групп, {len(items)} элементов)',
            received=f"Групп: {len(groups)}, элементов: {len(items)}"
        )