"""
Правило 11: Нумерованные списки.
Проверяет оформление нумерованных списков (раздел 11).
"""

import re
from lxml import etree
from .base_rule import BaseRule, RuleResult

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


class NumberedListsRule(BaseRule):
    @property
    def rule_id(self): return "numbered_lists"
    @property
    def name(self): return "Нумерованные списки"
    @property
    def description(self): return "Проверка оформления нумерованных списков (раздел 11)"

    def check(self, model):
        errors = []

        # Отбираем нумерованные: не начинаются с тире/дефиса И маркер decimal
        numbered_items = []
        for li in model.list_items:
            if not re.match(r'^[—–\-]', li['text']):
                marker = self._get_list_marker(model.doc, li)
                if marker == 'decimal' or (marker and marker.isdigit()):
                    numbered_items.append(li)
                elif marker is None:
                    # Не удалось определить — проверяем по тексту
                    if re.match(r'^\d+[\.\)]', li['text']):
                        numbered_items.append(li)

        if not numbered_items:
            return RuleResult(status='pass', summary='Нумерованные списки не найдены')

        # Группируем
        numbered_items.sort(key=lambda x: x['index'])
        groups = []
        cur = [numbered_items[0]]
        for i in range(1, len(numbered_items)):
            if numbered_items[i]['index'] == cur[-1]['index'] + 1:
                cur.append(numbered_items[i])
            else:
                groups.append(cur)
                cur = [numbered_items[i]]
        groups.append(cur)

        for group in groups:
            for idx, item in enumerate(group):
                text = item['text']
                pv = text[:50] + ('...' if len(text) > 50 else '')

                # Проверяем маркер
                marker = self._get_list_marker(model.doc, item)

                # Формат номера — должна быть точка, не скобка
                if re.match(r'^\d+\)', text):
                    errors.append(f"'{pv}': после номера должна быть точка, а не скобка")

                # Если маркер определён и это не decimal — ошибка
                if marker is not None and marker != 'decimal' and not marker.isdigit():
                    errors.append(f"'{pv}': маркер '{marker}' — должен быть числовой (decimal)")

                # Пунктуация
                content = re.sub(r'^\d+[\.\)]\s*', '', text)
                if content:
                    if content[0].isalpha() and content[0].islower():
                        errors.append(f"'{pv}': текст должен начинаться с прописной буквы")
                    if not content.rstrip().endswith('.'):
                        errors.append(f"'{pv}': элемент должен заканчиваться точкой")

                # Форматирование
                fn = item.get('font_name')
                if fn and 'times new roman' not in fn.lower():
                    errors.append(f"'{pv}': шрифт {fn}")

                fs = item.get('font_size_pt')
                if fs is not None and abs(fs - 14) > 0.5:
                    errors.append(f"'{pv}': размер {fs:.0f} пт (нужен 14)")

                if item.get('alignment') is not None and item['alignment'] != 3:
                    errors.append(f"'{pv}': выравнивание по ширине")

                ls = item.get('line_spacing')
                if ls is not None and isinstance(ls, (int, float)) and abs(ls - 1.5) > 0.1:
                    errors.append(f"'{pv}': междустрочный {ls:.2f} (нужен 1.5)")

                li_val = item.get('left_indent')
                if li_val is not None and abs(li_val) > 0.1:
                    errors.append(f"'{pv}': отступ слева {li_val:.1f} см (должен 0)")

                fi = item.get('first_line_indent')
                if fi is not None and abs(fi - 1.25) > 0.3:
                    errors.append(f"'{pv}': отступ первой строки {fi:.1f} см (нужен 1.25)")

        if errors:
            return RuleResult(
                status='fail', summary=f'Нарушений в нумерованных списках: {len(errors)}',
                details=errors,
                received=f"Групп: {len(groups)}, элементов: {len(numbered_items)}",
                expected="Точка после номера, прописная буква, точка в конце, "
                         "Times New Roman 14pt, по ширине, межстрочный 1.5, отступ слева 0, маркер 1.25"
            )

        return RuleResult(
            status='pass',
            summary=f'Нумерованные списки оформлены правильно',
            received=f"Групп: {len(groups)}, элементов: {len(numbered_items)}"
        )

    def _get_list_marker(self, doc, item):
        try:
            para = doc.paragraphs[item['para_index']]
            numPr = para._element.find(f'.//{{{W}}}numPr')
            if numPr is None:
                return None
            numId = numPr.find(f'{{{W}}}numId')
            if numId is None:
                return None
            numIdVal = numId.get(f'{{{W}}}val')

            numbering = doc._element.find(f'{{{W}}}numbering')
            if numbering is None:
                return None

            for num in numbering.findall(f'{{{W}}}num'):
                if num.get(f'{{{W}}}numId') == numIdVal:
                    lvl = num.find(f'{{{W}}}lvl[@w:ilvl="0"]')
                    if lvl is None:
                        lvl = num.find(f'{{{W}}}lvl')
                    if lvl is not None:
                        numFmt = lvl.find(f'{{{W}}}numFmt')
                        if numFmt is not None:
                            fmt = numFmt.get(f'{{{W}}}val')
                            if fmt == 'bullet':
                                lvlText = lvl.find(f'{{{W}}}lvlText')
                                if lvlText is not None:
                                    return lvlText.get(f'{{{W}}}val', '•')
                            return fmt
        except:
            pass
        return None